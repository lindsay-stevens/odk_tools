import os
import errno
import shutil
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
    sid = document.getroot().xpath(sid_xpath, namespaces=namespaces)[0]
    sid.text = '{0}{1}-'.format(sid.text, site_code)
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
    return images_dir


def copy_images_for_languages(image_dir, images, site_img_dir, languages):
    # copy from the media folder any files ending with the language name
    for image in images:
        image_file_name = os.path.splitext(image)[0]
        for lang in languages:
            if image_file_name.endswith(lang):
                out_path = os.path.join(site_img_dir, image)
                in_path = os.path.join(image_dir, image)
                shutil.copy2(in_path, out_path)


def main(xform, site_languages):
    directory = os.path.dirname(xform)
    file_name = os.path.basename(xform)
    settings = read_site_language_list(site_languages)
    image_dir_name = '{0}-media'.format(os.path.splitext(file_name)[0])
    image_dir = os.path.join(directory, image_dir_name)
    images = os.listdir(image_dir)

    for site in settings:
        # copy the images over for the languages available
        site_img_dir = create_output_directory(
                directory, site[2], image_dir_name)
        copy_images_for_languages(image_dir, images, site_img_dir, site[0])

        # read in the xform, remove not required languages, write out xform
        doc, nsp = read_xform(xform)
        doc = remove_xform_languages(doc, nsp, site[0])
        add_default_sid(doc, nsp, site[2])
        doc.write(os.path.join(directory, site[2], file_name))


FILE_PATH_IN = "C:/Users/Lstevens/Documents/repos/odk_tools/odk_tools/lang_split/test/R1309_BEHAVE.xml"
SITE_LANGS = "C:/Users/Lstevens/Documents/repos/odk_tools/odk_tools/lang_split/test/site_languages.xlsx"
main(FILE_PATH_IN, SITE_LANGS)
