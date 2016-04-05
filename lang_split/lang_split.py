import argparse
import time
import os
import errno
import shutil
import subprocess
import concurrent.futures
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


def add_default_sid(document, namespaces, site_code, file_name_base):
    # find the subject id element and append the site code to the default value
    sid_xpath = './/xf:instance//xf:visit/xf:sid'
    sid = document.getroot().xpath(sid_xpath, namespaces=namespaces)
    results = len(sid)
    skip_msg = 'Skipped adding site code to SID for {0} to form {1}: {2}.'
    # proceed if the sid element was found
    if results == 1:
        sid[0].text = '{0}{1}-'.format(sid[0].text, site_code)
        add_msg = 'Added site code to SID for {0} to form {1}.'
        print(add_msg.format(site_code, file_name_base))
    # print a warning and continue if the sid element was not found
    elif results == 0:
        print(skip_msg.format(site_code, file_name_base, '0 SID items found'))
    else:
        print(skip_msg.format(site_code, file_name_base, '>1 SID item found'))
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

    settings = read_site_language_list(site_languages)
    
    zip_jobs = list()
    site_dirs = list()

    for site in settings:
        languages = site[0]
        site_code = site[2]

        # copy the images over for the languages available
        site_dir_img, site_dir = create_output_directory(
                editions, site_code, image_dir_name)
        copy_images_for_languages(image_dir, images, site_dir_img, languages)

        # read in the xform, remove not required languages, write out xform
        doc, nsp = read_xform(xform)
        doc = remove_xform_languages(doc, nsp, languages)

        add_default_sid(doc, nsp, site_code, file_name_base)
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
