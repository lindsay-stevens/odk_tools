import argparse
import time
import os
import errno
import shutil
import subprocess
from lxml import etree
from xlrd import open_workbook


def read_xform(file_path):
    # read the xform xml document
    document = etree.parse(file_path)

    # modify the namespace map so that 'xf' is the alias for the default (None)
    root_element = document.getroot()
    namespaces = {k: v for k, v in root_element.nsmap.items() if k}
    namespaces['xf'] = root_element.nsmap[None]
    return document, namespaces


def remove_xform_languages(document, namespaces, languages):
    # locate the translation elements
    trans = document.getroot().xpath('.//xf:translation', namespaces=namespaces)
    for lang in trans:
        # remove languages not in the language list for the site
        if lang.attrib['lang'] not in languages:
            lang.getparent().remove(lang)

        # set the first listed language to the default
        if lang.attrib['lang'] == languages[0]:
            lang.attrib['default'] = 'true()'
        else:
            if 'default' in lang.attrib:
                del lang.attrib['default']
    return document


def add_default_sid(document, namespaces, site_code):
    # find the subject id element and append the site code to the default value
    sid_xpath = './/xf:instance//xf:visit/xf:sid'
    sid = document.getroot().xpath(sid_xpath, namespaces=namespaces)
    results = len(sid)
    # proceed if the sid element was found
    if results == 1:
        sid[0].text = '{0}{1}-'.format(sid[0].text, site_code)
    # print a warning and continue if the sid element was not found
    else:
        warn_fmt = 'Warn: Expected 1 instance sid element, found: {0}'
        print(warn_fmt.format(results))
    return document


def read_site_language_list(file_path):
    # read in the site languages spreadsheet, first sheet only
    workbook = open_workbook(filename=file_path)
    sheet = workbook.sheet_by_index(0)
    settings = list()

    # convert the languages list to a list
    # convert the site code to a string representation of an integer (not float)
    for row in sheet._cell_values[1:]:
        row[0] = row[0].lower().split('/')
        row[2] = str(int(row[2]))
        settings.append(row)
    return settings


def create_output_directory(file_path, site_code, image_dir_name):
    # create the directory for the site and xform media
    output_directory = os.path.join(file_path, site_code)
    images_dir = os.path.join(output_directory, image_dir_name)
    try:
        os.makedirs(images_dir)
    except OSError:
        if OSError.errno != errno.EEXIST:
            pass  # raise
    return images_dir, output_directory


def copy_images_for_languages(image_dir, images, site_img_dir, languages):
    # copy from the media folder any files ending with the language name
    for image in images:
        image_file_name = os.path.splitext(image)[0]
        for lang in languages:
            if image_file_name.endswith(lang):
                out_path = os.path.join(site_img_dir, image)
                in_path = os.path.join(image_dir, image)
                shutil.copy2(in_path, out_path)


def lang_split(xform, site_languages, path_to_7zip):
    directory = os.path.dirname(xform)
    editions = os.path.join(directory, 'editions')
    file_name = os.path.basename(xform)
    file_name_base = os.path.splitext(file_name)[0]

    image_dir_name = '{0}-media'.format(file_name_base)
    image_dir = os.path.join(directory, image_dir_name)
    images = os.listdir(image_dir)

    settings = read_site_language_list(site_languages)

    for site in settings:
        languages = site[0]
        site_code = site[2]

        # copy the images over for the languages available
        site_dir_img, site_dir = create_output_directory(
                editions, site_code, image_dir_name)
        copy_images_for_languages(image_dir, images, site_dir_img, languages)

        # read in the xform, remove not required languages, write out xform
        doc, nsp = read_xform(xform)
        doc = remove_xform_languages(doc, nsp, site_code)

        add_default_sid(doc, nsp, site_code)
        xform_out = os.path.join(site_dir, file_name)
        doc.write(xform_out)

        # use 7zip to compress the files and remove them afterwards
        zip_file_name = '{0}-{1}.7z'.format(file_name_base, site_code)
        zip_file_path = os.path.join(editions, zip_file_name)
        zip_fmt = '{0} a -t7z -mx9 -sdel {1} "{2}/*"'.format(
                path_to_7zip, zip_file_path, site_dir)
        subprocess.Popen(zip_fmt, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        # while the site directory is empty, wait 100ms then check again
        while os.listdir(site_dir):
            time.sleep(0.1)
        # once the site directory is empty, remove it and move on to next site.
        os.rmdir(site_dir)


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
