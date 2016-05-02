import os
import re
import argparse
import textwrap
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
from xlrd import open_workbook
from itertools import chain


class Images:
    """Prepares and writes images for a given language's settings."""

    @staticmethod
    def write(xlsform_path, settings):
        """
        Create images for all questions in the provided settings.

        Files will be placed in a folder adjacent to the xlsform.

        Parameters.
        :param xlsform_path: str. Path to xlsform.
        :param settings: dict.
        """
        output_path = Images._create_output_directory(xlsform_path)
        base_image, pixels_from_top = Images._prepare_base_image(
            settings=settings, xlsform_path=xlsform_path)
        image_generator = Images._prepare_question_images(
            base_image=base_image, pixels_from_top=pixels_from_top,
            settings=settings, output_path=output_path,
            xlsform_path=xlsform_path)
        for image, image_path in image_generator:
            image.save(image_path, 'PNG', dpi=[300, 300])
            image.close()

    @staticmethod
    def _prepare_base_image(settings, xlsform_path):
        """
        Create a base image for questions to use, possibly with a logo.

        In subsequent image processing functions, pixels_from_top is used to
        keep track of the current vertical offset as elements are added to
        the base image.

        Parameters.
        :param settings: dict. Image settings for a language.
        :param xlsform_path: str. Path to xlsform.
        :return: PIL.Image (base image), int (current pixels_from_top)
        """
        pixels_from_top = 0
        base_image = Images._create_blank_image(
            width=settings['image_width'], height=settings['image_height'],
            color=settings['image_color'])

        if len(settings['logo_image_path']) > 0:
            logo = Images._open_image(image_path=settings['logo_image_path'],
                                      xlsform_path=xlsform_path)
            base_image, pixels_from_top = Images._paste_image(
                base_image=base_image, pixels_from_top=pixels_from_top,
                paste_image=logo,
                pixels_before=settings['logo_image_pixels_before'],
                max_height=settings['logo_image_height'])

        return base_image, pixels_from_top

    @staticmethod
    def _prepare_question_images(base_image, pixels_from_top, settings,
                                 output_path, xlsform_path):
        """
        Add relevant text and image elements to a base image.

        Returns the image object and the intended output path, for another
        procedure to call Image.save() with the desired parameters.

        Parameters.
        :param base_image: PIL.Image to add elements to.
        :param pixels_from_top: int. current pixels from top (0 if no logo).
        :param settings: dict. Questions and their content for a language.
        :param output_path: str. Path to write images to.
        :param xlsform_path: str.
        :return: PIL.Image (question image) and str (image output path).
        """
        pixels_from_top_base = pixels_from_top
        for question in settings['image_content']:
            question_image = base_image.copy()
            pixels_from_top = pixels_from_top_base
            if len(question['text_label_column']) > 0:
                question_image, pixels_from_top, over_sized_labels = \
                    Images._draw_text(
                        base_image=question_image,
                        pixels_from_top=pixels_from_top,
                        pixels_before=settings['text_label_pixels_before'],
                        pixels_between=settings['text_label_pixels_line'],
                        **settings['label_font_kwargs'],
                        text=question['text_label_column'])
                if len(over_sized_labels) > 0:
                    print(settings['language'], over_sized_labels)
            if len(question['text_hint_column']) > 0:
                question_image, pixels_from_top, over_sized_hints = \
                    Images._draw_text(
                        base_image=question_image,
                        pixels_from_top=pixels_from_top,
                        pixels_before=settings['text_hint_pixels_before'],
                        pixels_between=settings['text_hint_pixels_line'],
                        **settings['hint_font_kwargs'],
                        text=question['text_hint_column'])
                if len(over_sized_hints) > 0:
                    print(settings['language'], over_sized_hints)
            if len(question['nest_image_column']) > 0:
                nest = Images._open_image(
                    image_path=question['nest_image_column'],
                    xlsform_path=xlsform_path)
                question_image, pixels_from_top = Images._paste_image(
                    base_image=question_image, pixels_from_top=pixels_from_top,
                    paste_image=nest,
                    pixels_before=settings['nest_image_pixels_before'],
                    max_height=None)
            question_path = os.path.join(
                output_path, '{0}_{1}.png'.format(
                    question['file_name_column'], settings['language']))
            yield question_image, question_path

    @staticmethod
    def _create_output_directory(xlsform_path):
        """
        Create a directory for the output image files next to the xlsform.

        The folder will be named like "INPUT_FILENAME-media' where the provided
        file path ends in 'INPUT_FILENAME.xlsx'. The directory will be in the
        same folder as the xlsform.

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
    def _create_blank_image(width, height, color):
        """
        Create a blank image for drawing or pasting content onto.

        Parameters.
        :param width: int. Image width.
        :param height: int. Image height.
        :param color: str. HTML common name of the image color.
        :return: PIL.Image. Object for adding existing content.
        """
        return Image.new('RGB', (width, height), color)

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
    def _draw_text(base_image, pixels_from_top, pixels_before,
                   pixels_between, font, font_color, text, image_margin=10):
        """
        Draw text onto an image.

        If a text line exceeds the base_image dimensions minus the image_margin
        then a tuple of the following elements:
        - dimension: 'width' or 'height'
        - line: the text line that was affected
        - size: the size of the line in the dimension.

        Parameters.
        :param base_image: PIL.Image. Image to draw text onto.
        :param pixels_from_top: int. Current pixel vertical offset.
        :param pixels_before: int. Pixel spacing from previous element.
        :param pixels_between: int. Pixel spacing between text lines.
        :param font: PIL.ImageFont. Font to use for drawing text.
        :param font_color: str. HTML common name of the font color.
        :param text: list. Text to draw onto the image.
        :return: PIL.Image (modified base_image), int (new vertical offset),
            tuple (oversize lines [see above description]).
        """
        pixels_from_top += pixels_before
        base_image_x, base_image_y = base_image.size

        drawer = ImageDraw.Draw(base_image)
        last_text_line = text[-1]
        oversize_lines = []

        for line in text:
            text_x, text_y = drawer.textsize(line, font=font)
            draw_position_x = int((base_image_x - text_x) / 2)
            draw_position_y = pixels_from_top
            drawer.text((draw_position_x, draw_position_y), line, font=font,
                        fill=font_color)
            pixels_from_top_add = text_y
            if line != last_text_line:
                pixels_from_top_add += pixels_between
            pixels_from_top += pixels_from_top_add
            if text_x > (base_image_x - image_margin):
                oversize_lines.append(('width', line, text_x))
            if (draw_position_y + text_y) > (base_image_y - image_margin):
                oversize_lines.append(('height', line, text_y))

        return base_image, pixels_from_top, oversize_lines

    @staticmethod
    def _open_image(image_path, xlsform_path):
        """
        Try to open an image from the provided path, or as a relative path.

        Parameters.
        :param image_path: str. Path to image to attempt to open.
        :param xlsform_path: str. Path to xlsform.
        :return: PIL.Image The opened image.
        """
        try:
            return Image.open(image_path)
        except FileNotFoundError:
            pass
        try:
            join_path = os.path.join(xlsform_path, image_path)
            return Image.open(join_path)
        except FileNotFoundError as fe:
            msg = "Failed to open {0} as relative or absolute path. " \
                  "Please check that the images exist in the locations that " \
                  "are referred to in the xlsform.".format(image_path)
            raise FileNotFoundError(msg, fe)


class ImageSettings:
    """Reads the image settings."""

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
            settings['label_font_kwargs'] = ImageSettings._get_font_kwargs(
                settings, 'label')
            settings['hint_font_kwargs'] = ImageSettings._get_font_kwargs(
                settings, 'hint')
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

    @staticmethod
    def _get_font_kwargs(settings, label_or_hint):
        """
        Make a dictionary with font kwargs from the image settings.

        Parameters.
        :param settings: dict. Image settings for a language.
        :param label_or_hint: str. Get font kwargs for 'label' or 'hint' text.
        :return: dict. Font kwargs.
        """
        font_kwargs = {
            'font': ImageFont.truetype(
                font=settings['text_{0}_font_name'.format(label_or_hint)],
                size=settings['text_{0}_font_size'.format(label_or_hint)]),
            'font_color': settings['text_{0}_font_color'.format(label_or_hint)]
        }
        return font_kwargs


class ImageContent:
    """Reads the image content for a given language's settings."""

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
            if i['item_type'] not in settings['type_ignore_list']:
                i['text_label_column'] = ImageContent._wrap_text(
                    i['text_label_column'], settings['text_label_wrap_char'])
                i['text_hint_column'] = ImageContent._wrap_text(
                    i['text_hint_column'], settings['text_hint_wrap_char'])
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
            if heading_value == 'type':
                column_locations['item_type'] = column_index
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


def write_images(xlsform_path):
    """
    Creates images for all languages and questions in the given xlsform.

    Parameters.
    :param xlsform_path: str. Path to xlsform to process.
    """
    xlsform_workbook = open_workbook(filename=xlsform_path)
    settings = ImageSettings.read(xlsform_workbook=xlsform_workbook)
    for index, language in settings.items():
        language = ImageContent.read(
            xlsform_workbook=xlsform_workbook, settings=language)
        Images.write(xlsform_path=xlsform_path, settings=language)


def _create_parser():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "xlsform",
        help="Path to the Excel XSLX file with the XLSForm definition. "
             "The a folder with the name [XFormName]-media will be created "
             "in the same folder, which will contain the image files.")
    return parser


def main_cli():
    """
     and run the script accordingly.
    """
    parser = _create_parser()
    args = parser.parse_args()
    write_images(xlsform_path=args.xlsform)


if __name__ == '__main__':
    main_cli()
