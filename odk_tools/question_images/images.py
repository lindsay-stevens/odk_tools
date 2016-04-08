import os
import re
import argparse
import textwrap
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from xlrd import open_workbook

"""
Creates image files with xlsform question text.

Run on command line with "-f" parameter which is path to xlsform file.
Image settings sheet must have all parameters set. Can process multiple langs.
Places images into "FILENAME-media" subfolder of xlsform file directory.
Requires PIL and xlrd, written with python 2.7.6; updated to work with 
python 3.4 by changing xrange to range ("seems to work", not tested).
"""
WARN_FMT = 'Warning: text line width exceeds image width for: {0} : {1}'


def write_image_text(draw, pixels_from_top, mode, **kwargs):
    """
    Writes the supplied text onto the base image and returns the spacing.

    The text should already have been wrapped to fit the image using wrap_text.
    """

    # get the text font
    font = ImageFont.truetype(
        kwargs['{0}_font_name'.format(mode)],
        int(kwargs['{0}_font_size'.format(mode)])
    )

    # set the current spacing, write the text, update the current spacing
    pixels_from_top += kwargs['{0}_pixels_before'.format(mode)]
    for line in kwargs[mode]:
        text_width, text_height = draw.textsize(line, font=font)
        draw.text(((kwargs['image_width'] - text_width) / 2, pixels_from_top),
                  line, font=font, fill=kwargs['{0}_font_color'.format(mode)])
        pixels_from_top += text_height + int(
            kwargs['{0}_pixels_line'.format(mode)]
        )
        if int(text_width) > int(kwargs['image_width']):
            print(WARN_FMT.format(kwargs['file_name'], line))
    # return the current spacing for further use
    return pixels_from_top


def write_image_paste(image, pixels_from_top, mode, **kwargs):
    """
    Pastes the supplied image onto the base image and returns the spacing.

    Images are re-sized with aspect ratio retained, constrained by image_width
    Logo image height is constrained by logo_image_height
    Nest image height is constrained by remaining base image height
    """

    paste_image_path = os.path.join(
        kwargs['file_path'], kwargs['{0}_image_path'.format(mode)]
    )
    # paste specified image onto the base image, centered and sized

    paste_image = Image.open(paste_image_path)
    paste_image_y = int(
        pixels_from_top + kwargs['{0}_image_pixels_before'.format(mode)]
    )
    if mode == 'logo':
        # resize the image to fill the desired space
        paste_image.thumbnail(
            (int(kwargs['image_width'] - 10),
             int(kwargs['logo_image_height']))
        )
    if mode == 'nest':
        # resize the image to fill remaining space, less a 10px margin
        paste_image.thumbnail(
            (int(kwargs['image_width'] - 10),
             kwargs['image_height'] - paste_image_y - 10)
        )
    paste_image_width, paste_image_height = paste_image.size
    paste_image_x = int((kwargs['image_width'] - paste_image_width) / 2)

    # paste the image and increment space remaining
    image.paste(paste_image, (paste_image_x, paste_image_y))
    pixels_from_top += paste_image_y + paste_image_height

    # return the current spacing for further use
    return image, pixels_from_top


def write_image(output_path, **kwargs):
    """
    Creates a base image, writes on the specified text and images and saves it.
    """

    # create the image and draw objects, and set the initial vertical spacing
    image = Image.new(
        'RGB', (int(kwargs['image_width']), int(kwargs['image_height'])),
        kwargs['image_color']
    )
    draw = ImageDraw.Draw(image)
    pixels_from_top = 0

    # if there is a logo, paste it on to the base image
    if 'logo_image_path' in kwargs:
        image, pixels_from_top = write_image_paste(
            image=image, pixels_from_top=pixels_from_top, mode='logo', **kwargs
        )

    # write each possible text type, write it to the image if it is available
    for mode in ['text_label', 'text_hint']:
        if mode in kwargs:
            pixels_from_top = write_image_text(
                draw=draw, pixels_from_top=pixels_from_top, mode=mode, **kwargs
            )

    # if there is a nested image, paste it on to the base image
    if 'nest_image_path' in kwargs:
        image, pixels_from_top = write_image_paste(
            image=image, pixels_from_top=pixels_from_top, mode='nest', **kwargs
        )

    # write the file to the output_path as png file
    item_filename_ext = os.path.join(
        output_path, '{0}.png'.format(kwargs['file_name']))
    image.save(item_filename_ext, 'PNG', dpi=[300, 300])


def wrap_text(text, wrap_chars):
    """
    Wraps a string to the specified characters, returning a list of strings.

    Text is split into paragraphs on sentence ending punctuation marks.
    Matches are 1+n characters that aren't one of (.?!) followed by one of (.?!)
    Punctuated abbreviations like "e.g." are split as sentences so avoid them.

    Each text paragraph is then wrapped into lines according to wrap_chars.
    After each paragraph, a spacer line is added.
    """

    # split text on sentence punctuation and remove empty strings
    text_paragraph = re.split('([^.?!]+[.?!])', text)
    text_paragraph = [i for i in text_paragraph if i != '']

    # wrap text lines, append space item for paragraph spacing line
    text_list = []
    for text_line in text_paragraph:
        text_line_wrap = textwrap.wrap(
            text_line, int(wrap_chars), break_on_hyphens=False
        )
        for text_line_wrap_line in text_line_wrap:
            text_list.append(text_line_wrap_line.strip())
        text_list.append(' ')

    # remove last added space item for paragraph spacing line, return list
    if len(text_list) > 0:
        while text_list[-1] == ' ':
            text_list.pop()

    return text_list


def read_xlsform(output_path, filepath):
    """
    Read form config from xls form file, write images to the output_path.

    Requires image_settings sheet with all configs set for each language
    Looks for survey sheet columns with same language, for example:
        image_settings sheet, text_label_column = label (for value::english)
        survey sheet, label#english is used for label text (for english)
    Images are named using item name and language, like myitem_english
    """

    # open the xlsform and read the image_settings
    xls_workbook = open_workbook(filename=filepath)
    xls_image_settings = xls_workbook.sheet_by_name(sheet_name='image_settings')

    image_settings_langs = {}
    for col_index in range(1, xls_image_settings.ncols):
        col_head_value = xls_image_settings.cell_value(0, col_index)
        if not col_head_value.find('::') == -1:
            image_settings_langs[col_index] = col_head_value.split('::')[1]

    for image_settings_lang in image_settings_langs:
        language = image_settings_langs[image_settings_lang]
        image_settings = {}
        for row_index in range(1, xls_image_settings.nrows):
            image_settings[xls_image_settings.cell_value(row_index, 0)]\
                = xls_image_settings.cell_value(row_index, image_settings_lang)

        # convert the languages and type_ignore_list strings to python lists
        image_settings['type_ignore_list']\
            = image_settings['type_ignore_list'].split(',')

        # read survey sheet into a list of dicts
        xls_survey = xls_workbook.sheet_by_name(sheet_name='survey')
        xls_survey_keys = [xls_survey.cell(0, col_index).value
                           for col_index in range(xls_survey.ncols)]
        xls_survey_rows = []
        for row_index in range(1, xls_survey.nrows):
            xls_survey_row = {xls_survey_keys[col_index]:
                              xls_survey.cell(row_index, col_index).value
                              for col_index in range(xls_survey.ncols)}
            xls_survey_rows.append(xls_survey_row)

        # for each language, write images for each item
        for xls_survey_item in xls_survey_rows:
            if xls_survey_item['type'] not in \
                    image_settings['type_ignore_list']:
                image_settings_kwargs = image_settings.copy()
                image_settings_kwargs['file_path'] = os.path.dirname(filepath)
                image_settings_kwargs['file_name'] = '{0}_{1}'.format(
                    xls_survey_item[image_settings_kwargs['file_name_column']],
                    language
                )
                for mode in ['text_label', 'text_hint']:
                    lang_col = '{0}#{1}'.format(
                        image_settings_kwargs['{0}_column'.format(mode)],
                        language
                    )
                    if lang_col in xls_survey_item:
                        image_settings_kwargs[mode] = wrap_text(
                            xls_survey_item[lang_col],
                            image_settings_kwargs[
                                '{0}_wrap_char'.format(mode)
                            ]
                        )
                if len(image_settings_kwargs['nest_image_column']):
                    nest_image_path = xls_survey_item['{0}#{1}'.format(
                        image_settings_kwargs['nest_image_column'], language)]
                    if len(nest_image_path) > 0:
                        image_settings_kwargs['nest_image_path'] = \
                            nest_image_path

                write_image(output_path, **image_settings_kwargs)


class Images(object):

    @staticmethod
    def _create_output_directory(xlsform_path):
        """
        Create a directory for the output image files next to the xlsform.

        The folder will be named like "INPUT_FILENAME-media' where the provided
        file path ends in 'INPUT_FILENAME.xlsx'. The directory will be in the same
        folder as the xlsform.

        If the directory exists already or there is some other problem with
        creating the directory, the exceptions will be raised / script exits.

        Parameters.
        :param xlsform_path: str. Path to input XLSX file.
        :return: str. Path to the output directory that was created.
        """
        output_folder = '{0}-media'.format(
            os.path.splitext(os.path.basename(xlsform_path))[0])
        output_path = os.path.join(os.path.dirname(xlsform_path), output_folder)
        os.makedirs(output_path)
        return output_path

    @staticmethod
    def _read_image_settings(xlsform_workbook):
        """
        Read the image settings from the xlsform workbook.

        The following steps are used:
        - identify the settings columns (contain '::' in the first row value)
        - read settings for all settings columns, named using the first column.

        Parameters.
        :param xlsform_workbook: xlrd workbook. XLSForm workbook object.
        :return: dict[dict]. Key is column index, value is dict of settings.
        """
        sheet = xlsform_workbook.sheet_by_name(sheet_name='image_settings')

        settings = dict()
        for column_index in range(1, sheet.ncols):
            heading_value = sheet.cell_value(0, column_index)
            if not heading_value.find('::') == -1:
                language = heading_value.split('::')[1]
                settings[column_index] = {'language': language}

        for k, v in settings.items():
            for i in range(1, sheet.nrows):
                name = sheet.cell_value(rowx=i, colx=0)
                value = sheet.cell_value(rowx=i, colx=k)
                if name == 'type_ignore_list':
                    v[name] = [x.strip() for x in value.split(',')]
                else:
                    v[name] = value

        return settings

    @staticmethod
    def _read_survey_values(xlsform_workbook, settings):
        """
        Read the survey values for each setting from the xlsform workbook.

        Parameters.
        :param xlsform_workbook: xlrd workbook. XLSForm workbook object.
        :param settings: dict. Image settings for each language.
        :return: dict[dict]. Key is column index, value is dict of settings.
        """
        pass


if __name__ == '__main__':
    # grab the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepath",
        help="Path to XLSForm file.")
    args = parser.parse_args()
    out_path = Images._create_output_directory(xlsform_path=args.filepath)
    read_xlsform(out_path, args.filepath)
