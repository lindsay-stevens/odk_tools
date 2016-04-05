import argparse
import time
import os
import errno
import shutil
import subprocess
import concurrent.futures
import logging
import sys
from lxml import etree
from xlrd import open_workbook


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('odk_tools.language_editions')


class Editions(object):

    @staticmethod
    def map_xf_to_xform_namespace(document):
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
    def update_xform_languages(document, namespaces, languages):
        """
        Remove translations that are not listed, and mark the first as default.

        Parameters
        :param document: etree.ElementTree. Document to remove from.
        :param namespaces: dict. Namespaces in the document.
        :param languages: list. Languages to keep.
        :return: etree.ElementTree. Document with languages updated.
        """
        # locate the translation elements
        translations = document.getroot().xpath(
            './/xf:translation', namespaces=namespaces)
        for t in translations:
            # remove languages not in the language list
            if t.attrib['lang'] not in languages:
                t.getparent().remove(t)

            # set the first listed language to the default
            if t.attrib['lang'] == languages[0]:
                t.attrib['default'] = 'true()'
            else:
                if 'default' in t.attrib:
                    del t.attrib['default']
        return document

    @staticmethod
    def add_site_to_default_sid(document, namespaces, site_code):
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
        logger.log(logging.INFO, log_msg.format(site_code, results, appended))
        return document

    @staticmethod
    def read_site_languages(file_path):
        """
        Read the list of sites and required languages from an XLSX file.

        - Look in the first sheet of the workbook.
        - First column is a '/' separated list of languages for the site.
        - Third column is the site code.

        Parameters.
        :params file_path: str. Path to site languages spreadsheet.
        :return: dict. Keys are site codes, values are language lists.
        """
        # read in the site languages spreadsheet, first sheet only
        workbook = open_workbook(filename=file_path)
        sheet = workbook.sheet_by_index(0)
        site_settings = dict()
        for row in sheet._cell_values[1:]:
            language_list = row[0].lower().split('/')
            site_code = str(int(row[2]))
            site_settings[site_code] = language_list
        return site_settings

    @staticmethod
    def create_output_directory(parent_folder, site_code, media_folder):
        """
        In the parent_folder, create a directory for the site files.

        Parameters.
        :params parent_folder: str. Path to the folder to create in.
        :params site_code: str. Site code, which will become the folder name.
        :params media_folder: str. The xform media folder name.
        """
        site_dir = os.path.join(parent_folder, site_code)
        media_dir = os.path.join(site_dir, media_folder)
        os.makedirs(media_dir, exist_ok=True)
        return site_dir, media_dir


def copy_images_for_languages(image_dir, images, site_img_dir, languages):
    # copy from the media folder any files ending with the language name
    for image in images:
        image_file_name = os.path.splitext(image)[0]
        for lang in languages:
            if image_file_name.endswith(lang):
                out_path = os.path.join(site_img_dir, image)
                in_path = os.path.join(image_dir, image)
                shutil.copy2(in_path, out_path)


def zip_concurrently(zip_jobs, site_dirs):
    run_args = {'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(subprocess.run, j, **run_args) for j in zip_jobs]
    results = concurrent.futures.wait(futures, timeout=180)
    for f in concurrent.futures.as_completed(futures):
        result = f.result()
        if result.returncode != 0:
            error_msg = 'Zip command returned an error code: {0}, {0}'
            print(error_msg.format(result.returncode, result.args))
    for site_dir in site_dirs:
        while os.listdir(site_dir):
            time.sleep(0.1)
        os.rmdir(site_dir)


def lang_split(xform, site_languages, path_to_7zip):
    directory = os.path.dirname(xform)
    editions = os.path.join(directory, 'editions')
    file_name = os.path.basename(xform)
    file_name_base = os.path.splitext(file_name)[0]

    image_dir_name = '{0}-media'.format(file_name_base)
    image_dir = os.path.join(directory, image_dir_name)
    images = os.listdir(image_dir)

    settings = Editions.read_site_languages(site_languages)
    
    zip_jobs = list()
    site_dirs = list()

    for site_code, languages in settings.items():

        # copy the images over for the languages available
        site_dir, site_dir_img = Editions.create_output_directory(
                editions, site_code, image_dir_name)
        copy_images_for_languages(image_dir, images, site_dir_img, languages)

        # read in the xform, remove not required languages, write out xform
        doc = etree.parse(xform)
        nsp = Editions.map_xf_to_xform_namespace(doc)
        doc = Editions.update_xform_languages(doc, nsp, languages)

        Editions.add_site_to_default_sid(doc, nsp, site_code)
        xform_out = os.path.join(site_dir, file_name)
        doc.write(xform_out)

        # use 7zip to compress the files and remove them afterwards
        zip_file_name = '{0}-{1}.zip'.format(file_name_base, site_code)
        zip_file_path = os.path.join(editions, zip_file_name)
        zip_fmt = '{0} a -tzip -mx9 -sdel {1} "{2}/{3}*"'.format(
                path_to_7zip, zip_file_path, site_dir, file_name_base)
        zip_jobs.append(zip_fmt)
        site_dirs.append(site_dir)

    zip_concurrently(zip_jobs, site_dirs)

if __name__ == '__main__':
    # grab the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--xform", help="path to xform xml file to split")
    parser.add_argument(
            "-l", "--sitelangs",
            help="path to xlsx file with sites and languages specified")
    parser.add_argument("-z", "--zipexe", help="path to 7zip.exe")
    args = parser.parse_args()
    lang_split(args.xform, args.sitelangs, args.zipexe)
