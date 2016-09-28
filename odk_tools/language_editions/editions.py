import argparse
import time
import os
import shutil
import subprocess
import concurrent.futures
import logging
from lxml import etree
from xlrd import open_workbook


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Editions:

    @staticmethod
    def _map_xf_to_xform_namespace(document):
        """
        Map 'xf' as the alias for the xforms namespace instead of None.

        Parameters
        :param document: etree.ElementTree. Document to read namespaces from.
        :return: dict
        """
        root_element = document.getroot()
        namespaces = {k: v for k, v in root_element.nsmap.items() if k}
        namespaces['xf'] = root_element.nsmap[None]
        return namespaces

    @staticmethod
    def _update_xform_languages(document, namespaces, languages):
        """
        Remove translations that are not listed, and mark the first as default.

        Parameters
        :param document: etree.ElementTree. Document to remove from.
        :param namespaces: dict. Namespaces in the document.
        :param languages: list. Languages to keep.
        :return: etree.ElementTree. Document with languages updated.
        """
        translations = document.getroot().xpath(
            './/xf:translation', namespaces=namespaces)
        for t in translations:
            if t.attrib['lang'] not in languages:
                t.getparent().remove(t)

            if t.attrib['lang'] == languages[0]:
                t.attrib['default'] = 'true()'
            else:
                if 'default' in t.attrib:
                    del t.attrib['default']
        return document

    @staticmethod
    def _add_site_to_default_sid(document, namespaces, site_code):
        """
        Find the SID form element and append the site code to the default value.

        Parameters.
        :param document: etree.ElementTree. Document to update.
        :param namespaces: dict. Namespaces in the document.
        :param site_code: str. Site code to add.
        :return: etree.ElementTree. Document with sid updated (if found).
        """
        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid = document.getroot().xpath(sid_xpath, namespaces=namespaces)
        results = len(sid)
        log_msg = 'Add to sid. Site code: {0}, SIDs found: {1}, Appended: {2}'
        appended = False
        if results == 1:
            sid[0].text = '{0}{1}-'.format(sid[0].text, site_code)
            appended = True
        logger.info(log_msg.format(site_code, results, appended))
        return document

    @staticmethod
    def _read_site_languages(file_path):
        """
        Read the list of sites and required languages from an XLSX file.

        - Look in the first sheet of the workbook.
        - First column is a '/' separated list of languages for the site.
        - Third column is the site code.

        Parameters.
        :params file_path: str. Path to site languages spreadsheet.
        :return: dict. Keys are site codes, values are language lists.
        """
        workbook = open_workbook(filename=file_path)
        sheet = workbook.sheet_by_index(0)
        site_settings = dict()
        for row in sheet._cell_values[1:]:
            language_list = [x.strip() for x in row[0].lower().split('/')]
            site_code = str(int(row[2]))
            site_settings[site_code] = language_list
        return site_settings

    @staticmethod
    def _create_output_directory(parent_path, site_code, media_folder,
                                 nest_in_odk_folders=0):
        """
        Create a directory for the site xform files in the parent folder.

        Parameters.
        :params parent_path: str. Path to the folder to create in.
        :params site_code: str. Site code, which will become the folder name.
        :params media_folder: str. The xform media folder name.
        :param nest_in_odk_folders: str. 1=yes, 0=no. Nest in /odk/forms/*.
        """
        site_dir = os.path.join(parent_path, site_code)
        if nest_in_odk_folders == 1:
            site_dir = os.path.join(site_dir, 'odk', 'forms')
        media_dir = os.path.join(site_dir, media_folder)
        os.makedirs(media_dir, exist_ok=True)
        return site_dir, media_dir

    @staticmethod
    def _copy_images_for_languages(source_path, target_path, languages):
        """
        Copy xform question images for the languages to the site folder.

        Images are matched to a language assuming the file naming convention of
        itemName_languageName.jpg.

        Parameters.
        :params source_path: str. Path to all xform images.
        :params target_path: str. Path to copy to.
        :params languages: list. Languages to copy images for.
        """
        copy_jobs = list()
        images = os.listdir(source_path)
        for image in images:
            image_file_name = os.path.splitext(image)[0]
            for lang in languages:
                if image_file_name.endswith(lang):
                    out_path = os.path.join(target_path, image)
                    in_path = os.path.join(source_path, image)
                    copy_jobs.append((in_path, out_path))
                    shutil.copy2(in_path, out_path)

    @staticmethod
    def _prepare_zip_job(z7zip_path, source_path, form_name, site_code):
        """
        Build a 7zip command string for archiving the site xform files.

        Parameters.
        :param z7zip_path: str. Path to 7zip executable.
        :param source_path: str. Path to site folder.
        :param form_name: str. XForm name.
        :param site_code: str. Site code.
        """
        target_file = '{0}.zip'.format(site_code)
        while not source_path.endswith(site_code):
            source_path = os.path.dirname(source_path)
            if len(source_path) == 0:
                break
        target_path = os.path.join(os.path.dirname(source_path), target_file)
        zip_fmt = '{0} a -tzip -mx9 -sdel "{1}" "{2}/*"'.format(
            z7zip_path, target_path, source_path)
        return zip_fmt

    @staticmethod
    def _execute_zip_jobs(jobs, concurrently=False):
        """
        Execute zip jobs.

        Parameters.
        :param jobs: list. 7zip command strings to execute.
        :param concurrently: bool. If True, use multiple processes.
        """
        logger.info('Running {0} zip jobs.'.format(len(jobs)))
        run_args = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE}
        error_msg = 'Zip command returned an error code: {0}, {0}'
        if concurrently:
            with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
                fut = [ex.submit(subprocess.run, j, **run_args) for j in jobs]
            results = [f.result() for f in concurrent.futures.as_completed(fut)]
        else:
            results = [subprocess.run(j, **run_args) for j in jobs]
        for r in results:
            if r.returncode != 0:
                logger.error(error_msg.format(r.returncode, r.args))
        logger.info('Zip jobs finished.')

    @staticmethod
    def _clean_up_empty_site_dirs(site_dirs):
        """
        Remove empty folders (whose contents were archived into zip folders).

        Parameters.
        :param site_dirs: list. Folders to be removed after archiving.
        """
        logger.info('Removing {0} site dirs.'.format(len(site_dirs)))
        for site_dir in site_dirs:
            while os.listdir(site_dir):
                time.sleep(0.1)
            os.rmdir(site_dir)
        logger.info('Site dirs removed.')

    @staticmethod
    def _prepare_site_files(output_path, xform_path, site_code, languages,
                            nest_in_odk_folders=0):
        """
        Prepare the files for a site edition.

        Parameters.
        :param xform_path: str. Path to xform being processed.
        :param site_code: str. Site code.
        :param languages: list. Languages applicable to the site.
        :param nest_in_odk_folders: str. 1=yes, 0=no. Nest in /odk/forms/*.
        :return site_path: str. Path to prepared site directory.
        """
        log_msg = 'Preparing files for site: {0}, languages: {1}'
        logger.info(log_msg.format(site_code, languages))
        parent_path = os.path.dirname(xform_path)

        xform_file_name_full = os.path.basename(xform_path)
        xform_file_name = os.path.splitext(xform_file_name_full)[0]
        xform_media_name = '{0}-media'.format(xform_file_name)
        xform_media_path = os.path.join(parent_path, xform_media_name)

        site_path, site_dir_img = Editions._create_output_directory(
            output_path, site_code, xform_media_name, nest_in_odk_folders)
        Editions._copy_images_for_languages(
            xform_media_path, site_dir_img, languages)

        doc = etree.parse(xform_path)
        nsp = Editions._map_xf_to_xform_namespace(doc)
        doc = Editions._update_xform_languages(doc, nsp, languages)
        doc = Editions._add_site_to_default_sid(doc, nsp, site_code)
        xform_out = os.path.join(site_path, xform_file_name_full)
        doc.write(xform_out)
        logger.info('Finished preparing site.')

        return site_path

    @staticmethod
    def language_editions(xform_path, site_languages, z7zip_path,
                          nest_in_odk_folders=0, concurrently=False):
        """
        Coordinate the other class methods to create xform language editions.

        Parameters.
        :param xform_path: str. Path to XForm file. It is assumed that the
            "xform-media" folder is in the same directory as the Xform.
        :param site_languages: str. Path to XLSX file specifying the sites to
            create editions for, and which languages each should get.
        :param z7zip_path: str. Path to 7zip executable.
        :param nest_in_odk_folders: str. 1=yes, 0=no. Nest in /odk/forms/*.
        :param concurrently: bool. Execute zip jobs concurrently, instead of
            sequentially. If running the script as a pyinstaller single exe,
            only sequential mode can work.
        """
        xform_path = os.path.abspath(xform_path)
        settings = Editions._read_site_languages(site_languages)
        xform_file_name = os.path.splitext(os.path.basename(xform_path))[0]
        output_path = os.path.join(os.path.dirname(xform_path), 'editions')

        zip_jobs = list()
        site_paths = list()
        for site_code, languages in settings.items():
            site_path = Editions._prepare_site_files(
                output_path, xform_path, site_code, languages,
                nest_in_odk_folders)
            zip_job = Editions._prepare_zip_job(
                z7zip_path, site_path, xform_file_name, site_code)
            zip_jobs.append(zip_job)
            while not site_path.endswith(site_code):
                site_path = os.path.dirname(site_path)
            site_paths.append(site_path)

        Editions._execute_zip_jobs(zip_jobs, concurrently)
        Editions._clean_up_empty_site_dirs(site_paths)


def write_editions(xform_path, site_languages, z7zip_path,
                   nest_in_odk_folders=0, concurrently=False):
    """
    Generate zip archives containing site-specific editions of an XForm.

    Parameters.
    :param xform_path: str. Path to XForm file. It is assumed that the
        "xform-media" folder is in the same directory as the Xform.
    :param site_languages: str. Path to XLSX file specifying the sites to
        create editions for, and which languages each should get.
    :param z7zip_path: str. Path to 7zip executable.
    :param nest_in_odk_folders: str. 1=yes, 0=no. Nest in /odk/forms/*.
    :param concurrently: bool. Execute zip jobs concurrently, instead of
        sequentially. If running the script as a pyinstaller single exe,
        only sequential mode can work.
    """
    Editions.language_editions(
        xform_path=xform_path, site_languages=site_languages,
        z7zip_path=z7zip_path, nest_in_odk_folders=nest_in_odk_folders,
        concurrently=concurrently)


def _create_parser():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "xform",
        help="Path to xform xml file to split by language.")
    parser.add_argument(
        "sitelangs",
        help="Path to xlsx file with sites and languages specified.")
    parser.add_argument(
        "--zipexe", dest='zipexe', default="C:\\Program Files\\7-Zip\\7z.exe",
        help="Path to 7zip executable, if not C:\\Program Files\\7-Zip\\7z.exe")
    parser.add_argument(
        "--concurrently", dest='concurrently',
        action='store_true', default=False,
        help="Run the zip jobs concurrently (up to 4 at a time), instead of"
             "sequentially. If running from a pyinstaller single exe, "
             "only sequential mode can work.")
    parser.add_argument(
        "--nested", dest="nested",
        action='store_const', default=0, const=1,
        help="Nest the output within each zip file inside additional "
             "subfolders 'odk/forms/*. This allows extracting the archive "
             "from the root folder of the device storage."
    )
    return parser


def main_cli():
    """
    Collect script arguments from stdin and run language_editions.
    """
    parser = _create_parser()
    args = parser.parse_args()
    logger.addHandler(logging.StreamHandler())
    write_editions(xform_path=args.xform, site_languages=args.sitelangs,
                   z7zip_path=args.zipexe, concurrently=args.concurrently,
                   nest_in_odk_folders=args.nested)


if __name__ == '__main__':
    main_cli()
