import os
import re
import argparse
import textwrap
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import PIL as pillow
from xlrd import open_workbook
from itertools import chain

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
    def write(xlsform_path, settings):
        """WIP: This should tie together all the image writing methods"""
        output_path = Images._create_output_directory(xlsform_path)
        base_image, base_vertical = Images._create_base_image(
            width=settings['image_width'],
            height=settings['image_height'],
            color=settings['image_color'])
        if len(settings['logo_image_path']) > 0:
            logo = pillow.Image.open(settings['logo_image_path'])
            base_image, base_vertical = Images._paste_image(
                base_image=base_image, pixels_from_top=base_vertical,
                paste_image=logo,
                pixels_before=settings['logo_image_pixels_before'],
                max_height=settings['logo_image_height'])

        label_font = pillow.ImageFont.truetype(
            font=settings['text_label_font_name'],
            size=settings['text_label_font_size'])
        label_font_color = settings['text_label_font_color']
        hint_font = pillow.ImageFont.truetype(
            font=settings['text_hint_font_name'],
            size=settings['text_hint_font_size'])
        hint_font_color = settings['text_hint_font_color']

        for question in settings['image_content'][0:3]:
            vertical = base_vertical
            question_image = base_image.copy()
            drawer = pillow.ImageDraw.Draw(question_image)
            if len(question['text_label_column']) > 0:
                question_image, vertical = Images._draw_text(
                    base_image=question_image,
                    drawer=drawer, pixels_from_top=vertical,
                    pixels_before=settings['text_label_pixels_before'],
                    pixels_between=settings['text_label_pixels_line'],
                    font=label_font, font_color=label_font_color,
                    text=question['text_label_column'])
            if len(question['text_hint_column']) > 0:
                question_image, vertical = Images._draw_text(
                    base_image=question_image,
                    drawer=drawer, pixels_from_top=vertical,
                    pixels_before=settings['text_hint_pixels_before'],
                    pixels_between=settings['text_hint_pixels_line'],
                    font=hint_font, font_color=hint_font_color,
                    text=question['text_hint_column'])
            if len(question['nest_image_column']) > 0:
                nest = pillow.Image.open(question['nest_image_column'])
                question_image, vertical = Images._paste_image(
                    base_image=question_image, pixels_from_top=vertical,
                    paste_image=nest,
                    pixels_before=settings['nest_image_pixels_before'],
                    max_height=None)
            item_filename_ext = os.path.join(
                output_path, '{0}_{1}.png'.format(
                    question['file_name_column'], settings['language']))
            question_image.save(item_filename_ext, 'PNG', dpi=[300, 300])

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
        os.makedirs(output_path, exist_ok=True)
        return output_path

    @staticmethod
    def _create_base_image(width, height, color):
        """
        Create a base image for drawing or pasting content onto.

        Parameters.
        :param width: int. Image width.
        :param height: int. Image height.
        :param color: str. HTML common name of the image color.
        :returns image: PIL.Image. Object for adding existing content.
        :returns drawer: PIL.ImageDraw. Object for creating new content.
        :returns pixels_from_top: int. Consumed vertical space.
        """
        image = pillow.Image.new('RGB', (int(width), int(height)), color)
        pixels_from_top = 0
        return image, pixels_from_top

    @staticmethod
    def _paste_image(base_image, pixels_from_top, paste_image,
                     pixels_before, max_height=None, image_margin=10):
        """
        Paste an image onto another, resizing if to fit if needed or requested.

        Parameters.
        :param base_image: PIL.Image. Image to paste onto.
        :param pixels_from_top: int. Current pixel vertical offset.
        :param paste_image: PIL.Image. Image to paste.
        :param pixels_before: int. Pixel spacing from previous element.
        :param max_height: int. Max pixel height for resizing paste_image.
        :param image_margin: int. Pixel width of border to reserve.
        :return: PIL.Image (modified base_image), int (new vertical offset).
        """
        pixels_from_top += pixels_before
        base_image_x, base_image_y = base_image.size

        paste_image_copy = paste_image.copy()
        paste_image_x, paste_image_y = paste_image.size

        if max_height is None:
            max_height = base_image_y - pixels_from_top
        leftover_y = base_image_y - pixels_from_top - max_height
        if leftover_y < image_margin:
            max_height -= image_margin

        resize_x = min(base_image_x - image_margin * 2, paste_image_x)
        resize_y = min(max_height, paste_image_y)
        paste_image_copy.thumbnail((resize_x, resize_y))
        resized_x, resized_y = paste_image_copy.size

        paste_position_x = int((base_image_x - resized_x) / 2)
        base_image.paste(paste_image_copy, (paste_position_x, pixels_from_top))
        pixels_from_top += resized_y
        return base_image, pixels_from_top

    @staticmethod
    def _draw_text(base_image, drawer, pixels_from_top, pixels_before,
                   pixels_between, font, font_color, text):
        pixels_from_top += pixels_before
        for line in text:
            text_x, text_y = drawer.textsize(line, font=font)
            base_image_x, base_image_y = base_image.size
            text_position_x = int((base_image_x - text_x) / 2)
            text_position_y = pixels_from_top
            drawer.text((text_position_x, text_position_y), line, font=font,
                        fill=font_color)
            pixels_from_top += text_y + pixels_between
            if text_x > base_image_x:
                print('image is too wide :(')

        return base_image, pixels_from_top


class ImageSettings:

    @staticmethod
    def read(xlsform_workbook):
        """
        Read image settings for each language from the xlsform workbook.

        Parameters.
        :param xlsform_workbook: xlrd workbook. XLSForm workbook object.
        :return: dict[dict]. Key is column index, value is dict of settings.
        """
        sheet = xlsform_workbook.sheet_by_name(sheet_name='image_settings')
        all_settings = ImageSettings._locate_language_settings_columns(
            image_settings_sheet=sheet)
        for column_index, settings in all_settings.items():
            settings.update(ImageSettings._read_language_settings_values(
                image_settings_sheet=sheet, column_index=column_index,
                settings=settings))
            settings['type_ignore_list'] = ImageSettings._csv_to_list(
                settings['type_ignore_list'])
        return all_settings

    @staticmethod
    def _csv_to_list(csv):
        """
        Convert a comma separated list of values to items of a list object.

        Parameters.
        :param csv: str. Comma separated values to split.
        :return: list. Object with each value as an item.
        """
        return [x.strip() for x in csv.split(',')]

    @staticmethod
    def _locate_language_settings_columns(image_settings_sheet):
        """
        Locate the column position and name of languages with image settings.

        Parameters.
        :param image_settings_sheet: xlrd sheet. Image settings worksheet.
        :return: dict. Column position and name of language settings.
        """
        settings = dict()
        for column_index in range(1, image_settings_sheet.ncols):
            heading_value = image_settings_sheet.cell_value(0, column_index)
            if not heading_value.find('::') == -1:
                language = heading_value.split('::')[1]
                settings[column_index] = {'language': language}
        return settings

    @staticmethod
    def _read_language_settings_values(
            image_settings_sheet, column_index, settings):
        """
        Read the image settings for each language in the image_settings sheet.

        Only supported settings are included, and the values are explicitly
        cast to the expected type.

        Parameters.
        :param image_settings_sheet: xlrd sheet. Image settings worksheet.
        :return: dict. Image settings for a language.
        """
        valid_names = ImageSettings._supported_settings()
        for i in range(1, image_settings_sheet.nrows):
            name = image_settings_sheet.cell_value(rowx=i, colx=0)
            value = image_settings_sheet.cell_value(rowx=i, colx=column_index)
            if name in valid_names.keys():
                settings[name] = valid_names[name](value)
        return settings

    @staticmethod
    def _supported_settings():
        """A dictionary of supported image setting names and their types."""
        general = {'language': str, 'file_name_column': str,
                   'type_ignore_list': str, 'image_width': int,
                   'image_height': int, 'image_color': str}
        logo = {'logo_image_path': str, 'logo_image_pixels_before': int,
                'logo_image_height': int}
        label = {'text_label_column': str, 'text_label_pixels_before': int,
                 'text_label_pixels_line': int, 'text_label_wrap_char': int,
                 'text_label_font_name': str, 'text_label_font_size': int,
                 'text_label_font_color': str}
        hint = {'text_hint_column': str, 'text_hint_pixels_before': int,
                'text_hint_pixels_line': int, 'text_hint_wrap_char': int,
                'text_hint_font_name': str, 'text_hint_font_size': int,
                'text_hint_font_color': str}
        nest_image = {'nest_image_column': str, 'nest_image_pixels_before': int}
        all_kw = {**general, **logo, **label, **hint, **nest_image}
        return all_kw


class ImageContent:

    @staticmethod
    def read(xlsform_workbook, settings):
        """
        Read image content values for each language from the xlsform workbook.

        The following steps are used:
        - identify the content columns specified in the language settings.
        - read item content values for all settings columns.

        Parameters.
        :param xlsform_workbook: xlrd workbook. XLSForm workbook object.
        :param settings: dict. Image settings for a language.
        :return: dict[dict]. Key is column index, value is dict of settings.
        """
        sheet = xlsform_workbook.sheet_by_name(sheet_name='survey')
        column_locations = ImageContent._locate_image_content_columns(
            survey_sheet=sheet, settings_values=settings)
        raw_image_content = ImageContent._read_survey_image_content_values(
            survey_sheet=sheet, column_locations=column_locations)

        image_content = list()
        for i in raw_image_content:
            if i['file_name_column'] not in settings['type_ignore_list']:
                i['text_label_column'] = ImageContent._wrap_text(
                    i['text_label_column'], settings['text_label_wrap_char'])
                i['text_hint_column'] = ImageContent._wrap_text(
                    i['text_hint_column'], settings['text_label_wrap_char'])
                image_content.append(i)

        settings['image_content'] = image_content
        return settings

    @staticmethod
    def _locate_image_content_columns(survey_sheet, settings_values):
        """
        Locate the column position of image content values.

        Parameters.
        :param survey_sheet: xlrd sheet. Survey worksheet.
        :param settings_values: dict. Image settings for a language.
        :return: dict. Column position and name of image content values.
        """
        settings_columns = (
            'text_label_column', 'text_hint_column', 'nest_image_column')
        column_locations = dict()
        content_columns = {settings_values[x]: x for x in settings_columns}

        for column_index in range(0, survey_sheet.ncols):
            heading_value = survey_sheet.cell_value(0, column_index)
            if heading_value == settings_values['file_name_column']:
                column_locations['file_name_column'] = column_index
            if not heading_value.find('#') == -1:
                heading_split = heading_value.split('#')
                column_name = heading_split[0]
                language_name = heading_split[1]
                if language_name == settings_values['language']:
                    column_lookup = content_columns.get(column_name)
                    if column_lookup is not None:
                        column_locations[column_lookup] = column_index

        return column_locations

    @staticmethod
    def _read_survey_image_content_values(survey_sheet, column_locations):
        """
        Read the image content in the specified locations from the survey sheet.

        Parameters.
        :param survey_sheet: xlrd sheet. Survey worksheet.
        :param column_locations: dict. Column locations of image content.
        :return: list. Image content values.
        """
        all_image_content = list()
        for row_index in range(1, survey_sheet.nrows):
            content = dict()
            for n, i in column_locations.items():
                content[n] = survey_sheet.cell_value(rowx=row_index, colx=i)
            all_image_content.append(content)
        return all_image_content

    @staticmethod
    def _wrap_text(text, wrap_characters):
        """
        Break text into a list based on punctuation (.?!) then wrap_characters.

        It's assumed that (.?!) mark sentence endings. When these are found,
        an extra newline is inserted to improved readability. Sentences are
        split if their length is greater than wrap_characters. Trailing and
        leading spaces are removed from sentence fragments.

        Parameters.
        :param text: str. Text to be wrapped.
        :param wrap_characters: int. Maximum sentence characters per line.
        :return: list. Text broken into sentence fragments.
        """
        punctuation_split = re.split('([^.?!]+[.?!])', text)
        non_empty_sentence = [i for i in punctuation_split if i != '']
        sentence_count = len(non_empty_sentence)
        paragraphs = []
        for i, sentence in enumerate(non_empty_sentence):
            sentence_fragments = textwrap.wrap(
                sentence, width=wrap_characters, break_on_hyphens=False)
            stripped_fragments = [f.strip() for f in sentence_fragments]
            paragraphs.append(stripped_fragments)
            if i < sentence_count - 1:
                paragraphs.append([' '])
        flatten_paragraphs = list(chain.from_iterable(paragraphs))
        return flatten_paragraphs


if __name__ == '__main__':
    # grab the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepath",
        help="Path to XLSForm file.")
    args = parser.parse_args()
    out_path = Images._create_output_directory(xlsform_path=args.filepath)
    read_xlsform(out_path, args.filepath)
