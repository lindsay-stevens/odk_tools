import argparse
import os
import logging
from lxml import etree
from xlrd import open_workbook
import zipfile
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
ZipJob = List[Tuple[str, str]]
ETree = etree.ElementTree
TupleStr = Tuple[str, ...]


class Editions:

    @staticmethod
    def _map_xf_to_xform_namespace(document: ETree) -> Dict[str, str]:
        """
        Map 'xf' as the alias for the xforms namespace instead of None.

        Parameters
        :param document: Document to read namespaces from.
        """
        root_element = document.getroot()
        namespaces = {k: v for k, v in root_element.nsmap.items() if k}
        namespaces['xf'] = root_element.nsmap[None]
        return namespaces

    @staticmethod
    def _update_xform_languages(document: ETree, namespaces: Dict[str, str],
                                languages: TupleStr) -> ETree:
        """
        Remove translations that are not listed, and mark the first as default.

        Parameters
        :param document: Document to remove from.
        :param namespaces: Namespaces in the document.
        :param languages: Languages to keep.
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
    def _add_site_to_default_sid(document: ETree, namespaces: Dict[str, str],
                                 site_code: str) -> ETree:
        """
        Find the SID form element and append the site code to the default value.

        Parameters.
        :param document: Document to update.
        :param namespaces: Namespaces in the document.
        :param site_code: Site code to add.
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
    def _read_site_languages(file_path: str) -> Dict[str, TupleStr]:
        """
        Read the list of sites and required languages from an XLSX file.

        - Look in the first sheet of the workbook.
        - First column is a '/' separated list of languages for the site.
        - Third column is the site code.

        Parameters.
        :params file_path: Path to site languages spreadsheet.
        """
        workbook = open_workbook(filename=file_path)
        sheet = workbook.sheet_by_index(0)
        site_settings = dict()
        for row in sheet._cell_values[1:]:
            languages = tuple(x.strip() for x in row[0].lower().split('/'))
            site_code = str(int(row[2]))
            site_settings[site_code] = languages
        return site_settings

    @staticmethod
    def _run_zip_jobs(output_path: str,
                      zip_jobs: List[Tuple[str, ZipJob, Tuple[str, str]]]):
        """
        Execute the provided zip jobs by creating and populating a zip file.

        :param zip_jobs: Zip jobs to execute.
        """
        compress = zipfile.ZIP_DEFLATED
        os.makedirs(output_path, exist_ok=True)
        dupe_msg = "Skipped duplicating file: {0}"
        for site_code, jobs, xform in zip_jobs:
            zip_name = os.path.join(output_path, "{0}.zip".format(site_code))
            existing_zip_items = list()
            if os.path.isfile(zip_name):
                with zipfile.ZipFile(file=zip_name, mode="r") as existing_zip:
                    for zip_item in existing_zip.namelist():
                        existing_zip_items.append(os.path.normpath(zip_item))
            with zipfile.ZipFile(
                    file=zip_name, mode="a", compression=compress) as zip_file:
                for source_file, archive_file in jobs:
                    archive_norm = os.path.normpath(archive_file)
                    if archive_norm in existing_zip_items:
                        logger.warning(dupe_msg.format(archive_norm))
                    else:
                        zip_file.write(source_file, archive_file)
                xform_filename, xform_data = xform
                xform_norm = os.path.normpath(xform_filename)
                if xform_norm in existing_zip_items:
                    logger.warning(dupe_msg.format(xform_norm))
                else:
                    zip_file.writestr(*xform)

    @staticmethod
    def _prepare_zip_jobs(source_path: str, languages: TupleStr) -> ZipJob:
        """
        Prepare path (to, from) pairs for use in ZipFile write job.

        Parameters.
        :param source_path: Path to copy files from.
        :param languages: Languages to filter the files lists for.
        """
        zip_jobs = []
        source_parent = os.path.dirname(source_path)
        for base, dirs, files in os.walk(source_path):
            for file in files:
                file_name = os.path.splitext(file)[0]
                for lang in languages:
                    if file_name.endswith(lang):
                        file_path = os.path.join(base, file)
                        arch_path = os.path.relpath(file_path, source_parent)
                        zip_jobs.append((file_path, arch_path))
        return zip_jobs

    @staticmethod
    def _prepare_site_job(xform_path: str, site_code: str,
                          languages: TupleStr, nest_in_odk_folders: int=0,
                          collect_settings: str=None
                          ) -> Tuple[ZipJob, Tuple[str, str]]:
        """
        Prepare the zip jobs and xform for a site.

        Parameters.
        :param xform_path: Path to xform being processed.
        :param site_code: Site code for the site to process.
        :param languages: Languages applicable to the site.
        :param nest_in_odk_folders: 1=yes, 0=no. Nest output in /odk/forms/*.
        :param collect_settings: Path to collect.settings file to include
            in nested output folders.
        """
        log_msg = 'Preparing files for site: {0}, languages: {1}'
        logger.info(log_msg.format(site_code, languages))

        xform_file_name = os.path.basename(xform_path)
        xform_name = os.path.splitext(xform_file_name)[0]
        xform_media_path = os.path.join(
            os.path.dirname(xform_path), '{0}-media'.format(xform_name))
        jobs = Editions._prepare_zip_jobs(
            source_path=xform_media_path, languages=languages)

        xform = etree.parse(xform_path)
        nsp = Editions._map_xf_to_xform_namespace(xform)
        xform = Editions._update_xform_languages(xform, nsp, languages)
        xform = Editions._add_site_to_default_sid(xform, nsp, site_code)
        xform = etree.tostring(xform)

        if nest_in_odk_folders == 1:
            nest_prefix = ('odk', 'forms')
            jobs = [(x, os.path.join(*nest_prefix, y)) for x, y in jobs]
            xform_file_name = os.path.join(
                *nest_prefix, os.path.basename(xform_path))
        if collect_settings is not None:
            arch_path = os.path.join(
                'odk', os.path.basename(collect_settings))
            jobs.append((collect_settings, arch_path))

        logger.info('Finished preparing site.')

        return jobs, (xform_file_name, xform)

    @staticmethod
    def _path_error_format(
            resource_name: str, expected: str, actual: str, ):
        return "Expected {0} for {1}, got {2}. " \
               "Please check the file path and correct it.".format(
                expected, resource_name, actual)

    @staticmethod
    def write_language_editions(
            xform_path: str, site_languages: str, nest_in_odk_folders: int=0,
            collect_settings: str=None):
        """
        Coordinate the other class methods to create xform language editions.

        Parameters.
        :param xform_path: Path to XForm file. It is assumed that the
            "xform-media" folder is in the same directory as the Xform.
        :param site_languages: Path to XLSX file specifying the sites to
            create editions for, and which languages each should get.
        :param nest_in_odk_folders: 1=yes, 0=no. Nest output in /odk/forms/*.
        :param collect_settings: Path to collect.settings file to include
            in nested output folders.
        """
        xform_path = os.path.abspath(xform_path)
        settings = Editions._read_site_languages(site_languages)
        output_path = os.path.join(os.path.dirname(xform_path), 'editions')

        xform_path_ext = os.path.splitext(xform_path)[1].upper()
        if xform_path_ext != ".XML":
            raise ValueError(Editions._path_error_format(
                resource_name="XForm", expected=".XML extension",
                actual=xform_path_ext))
        site_languages_ext = os.path.splitext(site_languages)[1].upper()
        if site_languages_ext != ".XLSX":
            raise ValueError(Editions._path_error_format(
                resource_name="Site languages", expected=".XLSX extension",
                actual=site_languages_ext))
        if collect_settings is not None:
            collect_settings_base = os.path.basename(collect_settings)
            if collect_settings_base != "collect.settings":
                raise ValueError(Editions._path_error_format(
                    resource_name="Collect Settings",
                    expected="collect.settings file",
                    actual=collect_settings_base))

        zip_jobs = list()
        for site_code, languages in settings.items():
            jobs, xform = Editions._prepare_site_job(
                xform_path=xform_path, site_code=site_code, languages=languages,
                nest_in_odk_folders=nest_in_odk_folders,
                collect_settings=collect_settings)
            zip_jobs.append((site_code, jobs, xform))

        logger.info('Running {0} zip jobs.'.format(len(zip_jobs)))
        Editions._run_zip_jobs(output_path, zip_jobs)
        logger.info('Zip jobs finished.')


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
        "--nested", dest="nested",
        action='store_const', default=0, const=1,
        help="Nest the output within each zip file inside additional "
             "subfolders 'odk/forms/*. This allows extracting the archive "
             "from the root folder of the device storage.")
    parser.add_argument(
        "--collect_settings", dest='collect_settings', default=None,
        help="Path to collect.settings file to add to the nested zip file.")
    return parser


def main_cli():
    """
    Collect script arguments from stdin and run language_editions.
    """
    parser = _create_parser()
    args = parser.parse_args()
    logger.addHandler(logging.StreamHandler())
    Editions.write_language_editions(
        xform_path=args.xform, site_languages=args.sitelangs,
        nest_in_odk_folders=args.nested, collect_settings=args.collect_settings)


if __name__ == '__main__':
    main_cli()
