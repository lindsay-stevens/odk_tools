import os
import shutil
import xlrd
from unittest import TestCase
from odk_tools.question_images.images import Images, ImageContent, \
    ImageSettings, write_images, _create_parser
from PIL import Image


class _TestImagesBase(TestCase):
    """Common properties for images module tests."""

    @classmethod
    def setUpClass(cls):
        cls.xlsform1 = 'Q1302_BEHAVE.xlsx'
        cls.test_output_folder = 'Q1302_BEHAVE-media'
        cls.xlsform1_workbook = xlrd.open_workbook(filename=cls.xlsform1)

    def setUp(self):
        self.clean_test_output_folder = False

    def tearDown(self):
        if self.clean_test_output_folder:
            shutil.rmtree(self.test_output_folder, ignore_errors=True)


class TestImages(_TestImagesBase):
    """Tests for functions in the Images module."""

    def test_write_multi_language(self):
        """Should create expected number of images for multi-language form."""
        self.clean_test_output_folder = True
        self.test_output_folder = 'Q1309_BEHAVE-media'
        xlsform = 'Q1309_BEHAVE.xlsx'
        write_images(xlsform_path=xlsform)
        output_files = os.listdir(self.test_output_folder)
        self.assertEqual(495, len(output_files))

    def test_write_single_language(self):
        """Should create expected number of images for single language form."""
        self.clean_test_output_folder = True
        write_images(xlsform_path=self.xlsform1)
        output_files = os.listdir(self.test_output_folder)
        self.assertEqual(184, len(output_files))

    def test_create_parser_without_args(self):
        """Should exit when no args provided."""
        with self.assertRaises(SystemExit):
            _create_parser().parse_args([])

    def test_create_parser_with_args(self):
        """Should parse the provided argument."""
        self.clean_test_output_folder = True
        input_arg = 'Q1302_BEHAVE.xlsx'
        args = _create_parser().parse_args([input_arg])
        self.assertEqual(input_arg, args.xlsform)


class TestImagesImage(_TestImagesBase):
    """Tests for Images class."""

    def test_create_output_directory(self):
        """Should create a folder with the expected name."""
        self.clean_test_output_folder = True
        shutil.rmtree(self.test_output_folder, ignore_errors=True)
        self.assertFalse(os.path.isdir(self.test_output_folder))
        Images._create_output_directory(self.xlsform1)
        self.assertTrue(os.path.isdir(self.test_output_folder))

    def test_create_output_directory_with_spaces(self):
        """Should create a folder with the expected name."""
        self.clean_test_output_folder = True
        self.test_output_folder = 'folder with spaces'
        test_file_path = 'folder with spaces/dummy_file.txt'
        shutil.rmtree(self.test_output_folder, ignore_errors=True)
        self.assertFalse(os.path.isdir(self.test_output_folder))
        Images._create_output_directory(test_file_path)
        self.assertTrue(os.path.isdir(self.test_output_folder))

    def test_create_output_directory_with_spaces_unc(self):
        """Should create a folder with the expected name."""
        self.clean_test_output_folder = True
        current_folder = os.path.dirname(__file__)
        test_folder = os.path.join(current_folder, 'folder with spaces')
        unc_path = '\\\\localhost\\c$' + test_folder[2:]
        self.test_output_folder = test_folder
        test_file_path = unc_path + '\\my_xlsform.xlsx'
        shutil.rmtree(self.test_output_folder, ignore_errors=True)
        self.assertFalse(os.path.isdir(self.test_output_folder))
        Images._create_output_directory(test_file_path)
        self.assertTrue(os.path.isdir(self.test_output_folder))

    def test_create_blank_image(self):
        """Should create an image of the expected size and colour."""
        observed = Images._create_blank_image(50, 10, 'lavender')
        self.assertEqual((50, 10), observed.size)
        lavender_rgb_values = (230, 230, 250)
        self.assertEqual(lavender_rgb_values, observed.load()[5, 5])

    def test_prepare_base_image_with_logo(self):
        """Should return a base image with a logo pasted onto it."""
        settings = {'image_width': 500, 'image_height': 500,
                    'image_color': 'white',
                    'logo_image_path': 'nest_images/stopc-logo.png',
                    'logo_image_pixels_before': 10,
                    'logo_image_height': 40}
        observed, _ = Images._prepare_base_image(settings)
        expected = Image.open('reference_images/base_logo.png')
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))
        expected.close()

    def test_prepare_base_image_no_logo(self):
        """Should return a base image with no logo."""
        settings = {'image_width': 500, 'image_height': 500,
                    'image_color': 'white', 'logo_image_path': ''}
        observed, _ = Images._prepare_base_image(settings)
        expected = Images._create_blank_image(500, 500, 'white')
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))

    def test_write_single_language(self):
        """Should create the expected number of images."""
        self.clean_test_output_folder = True
        settings = ImageSettings.read(xlsform_workbook=self.xlsform1_workbook)
        add_content = ImageContent.read(
            xlsform_workbook=self.xlsform1_workbook, settings=settings[2])
        Images.write(self.xlsform1, add_content)
        output_files = os.listdir(self.test_output_folder)
        self.assertEqual(184, len(output_files))


class TestImagesPrepareQuestionImages(_TestImagesBase):
    """Tests for Images._prepare_question_images()"""

    def setUp(self):
        super().setUp()
        template = ImageSettings.read(xlsform_workbook=self.xlsform1_workbook)
        settings = ImageContent.read(
            xlsform_workbook=self.xlsform1_workbook, settings=template[2])
        settings['image_content'] = [x for x in settings['image_content']
                                     if x['file_name_column'] == 'da2d10ye']
        self.settings = settings

    def test_all_content_types(self):
        """Should return image with label, hint and nested image."""
        settings = self.settings
        base_image, pixels_from_top = Images._prepare_base_image(
            settings=settings)
        observed, _ = list(Images._prepare_question_images(
            base_image=base_image, pixels_from_top=pixels_from_top,
            settings=settings, output_path=''))[0]
        expected = Image.open('reference_images/da2d10ye_english_all.png')
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))

    def test_label_only(self):
        """Should return image with label only."""
        settings = self.settings
        settings['image_content'][0]['text_hint_column'] = ''
        settings['image_content'][0]['nest_image_column'] = ''
        base_image, pixels_from_top = Images._prepare_base_image(
            settings=settings)
        observed, _ = list(Images._prepare_question_images(
            base_image=base_image, pixels_from_top=pixels_from_top,
            settings=settings, output_path=''))[0]
        expected = Image.open('reference_images/da2d10ye_english_label.png')
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))

    def test_label_and_hint_only(self):
        """Should return image with label only."""
        settings = self.settings
        settings['image_content'][0]['nest_image_column'] = ''
        base_image, pixels_from_top = Images._prepare_base_image(
            settings=settings)
        observed, _ = list(Images._prepare_question_images(
            base_image=base_image, pixels_from_top=pixels_from_top,
            settings=settings, output_path=''))[0]
        ref_image = 'reference_images/da2d10ye_english_label_hint.png'
        expected = Image.open(ref_image)
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))

    def test_label_and_nested_image_only(self):
        """Should return image with label and nested image."""
        settings = self.settings
        settings['image_content'][0]['text_hint_column'] = ''
        base_image, pixels_from_top = Images._prepare_base_image(
            settings=settings)
        observed, _ = list(Images._prepare_question_images(
            base_image=base_image, pixels_from_top=pixels_from_top,
            settings=settings, output_path=''))[0]
        ref_image = 'reference_images/da2d10ye_english_label_image.png'
        expected = Image.open(ref_image)
        self.assertEqual(list(expected.getdata()), list(observed.getdata()))


class TestImagesPasteImage(TestCase):
    """Tests for Images._paste_image()"""

    def test_shrink_tall_to_max_height(self):
        """Should resize to max_height."""
        pixels_from_top = 0
        base_image = Images._create_blank_image(500, 500, 'red')
        paste_image = Images._create_blank_image(750, 600, 'blue')
        pixels_before = 5
        max_height = 40
        expected = 45
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=max_height)
        self.assertEqual(expected, observed)

    def test_shrink_tall_to_max_height_with_y_offset(self):
        """Should resize to max_height."""
        base_image = Images._create_blank_image(500, 500, 'red')
        pixels_from_top = 100
        paste_image = Images._create_blank_image(750, 600, 'blue')
        pixels_before = 5
        max_height = 250
        expected = 355
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=max_height)
        self.assertEqual(expected, observed)

    def test_shrink_wide_to_available(self):
        """Should resize to width."""
        pixels_from_top = 0
        base_image = Images._create_blank_image(500, 500, 'red')
        paste_image = Images._create_blank_image(750, 600, 'blue')
        pixels_before = 5
        expected = 389
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_shrink_tall_to_available(self):
        """Should resize to height."""
        pixels_from_top = 0
        base_image = Images._create_blank_image(500, 500, 'red')
        paste_image = Images._create_blank_image(600, 750, 'blue')
        pixels_before = 5
        expected = 490
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_shrink_square_to_available(self):
        """Should resize to width."""
        pixels_from_top = 0
        base_image = Images._create_blank_image(500, 500, 'red')
        paste_image = Images._create_blank_image(600, 600, 'blue')
        pixels_before = 5
        expected = 485
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_shrink_square_to_available_with_y_offset(self):
        """Should resize to fit available space."""
        base_image = Images._create_blank_image(500, 500, 'red')
        pixels_from_top = 50
        paste_image = Images._create_blank_image(600, 600, 'blue')
        pixels_before = 5
        expected = 490
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_doesnt_alter_input_paste_image(self):
        """Resizing should be done on a copy, not the original."""
        base_image = Images._create_blank_image(500, 500, 'red')
        paste_image = Images._create_blank_image(600, 600, 'blue')
        expected = (600, 600)
        Images._paste_image(
            base_image=base_image, pixels_from_top=20,
            paste_image=paste_image, pixels_before=20, max_height=50)
        observed = paste_image.size
        self.assertEqual(expected, observed)


class TestImagesDrawText(_TestImagesBase):
    """Tests for Images._draw_text()"""

    def test_ideal_input(self):
        """Should return a modified image with expected offset and no errors."""
        settings = ImageSettings.read(xlsform_workbook=self.xlsform1_workbook)
        settings = settings[2]
        base_image = Images._create_blank_image(
            settings['image_width'], settings['image_height'],
            settings['image_color'])
        original_image = base_image.copy()
        text = ['This is some text', 'that is for a question']
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        drawn_image, vertical, oversize_lines = Images._draw_text(
            base_image=base_image, pixels_from_top=0, pixels_before=10,
            pixels_between=5, **font_kwargs, text=text)
        self.assertNotEqual(list(original_image.getdata()),
                            list(drawn_image.getdata()))
        self.assertEqual(79, vertical)
        self.assertEqual(0, len(oversize_lines))

    def test_line_exceeds_width(self):
        """Should return an error indicating the line that was too wide."""
        base_image = Images._create_blank_image(200, 200, 'white')
        text = ['This is some text that is for a question']
        settings = {'text_label_font_name': 'arialbd.ttf',
                    'text_label_font_size': 32,
                    'text_label_font_color': 'red'}
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        _, _, observed = Images._draw_text(
            base_image=base_image, pixels_from_top=0, pixels_before=10,
            pixels_between=5, **font_kwargs, text=text)
        expected = [('width', text[0], 589)]
        self.assertEqual(expected, observed)

    def test_line_exceeds_height(self):
        """Should return an error indicating the line that was too tall."""
        base_image = Images._create_blank_image(200, 100, 'white')
        text = ['Big', 'Text']
        settings = {'text_label_font_name': 'arialbd.ttf',
                    'text_label_font_size': 64,
                    'text_label_font_color': 'red'}
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        _, _, observed = Images._draw_text(
            base_image=base_image, pixels_from_top=0, pixels_before=10,
            pixels_between=5, **font_kwargs, text=text)
        expected = [('height', text[1], 59)]
        self.assertEqual(expected, observed)

    def test_line_exceeds_width_and_height(self):
        """Should return an errors indicating the line is too wide and tall."""
        base_image = Images._create_blank_image(50, 50, 'white')
        text = ['This is too big']
        settings = {'text_label_font_name': 'arialbd.ttf',
                    'text_label_font_size': 64,
                    'text_label_font_color': 'red'}
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        _, _, observed = Images._draw_text(
            base_image=base_image, pixels_from_top=0, pixels_before=10,
            pixels_between=5, **font_kwargs, text=text)
        expected = [('width', text[0], 436), ('height', text[0], 72)]
        self.assertEqual(expected, observed)

    def test_line_exceeds_width_and_height_multiple(self):
        """Should return an errors indicating which lines are too big."""
        base_image = Images._create_blank_image(50, 100, 'white')
        text = ['This text is too big', 'and so is this']
        settings = {'text_label_font_name': 'arialbd.ttf',
                    'text_label_font_size': 64,
                    'text_label_font_color': 'red'}
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        _, _, observed = Images._draw_text(
            base_image=base_image, pixels_from_top=0, pixels_before=10,
            pixels_between=5, **font_kwargs, text=text)
        expected = [('width', text[0], 568),
                    ('width', text[1], 411), ('height', text[1], 59)]
        self.assertEqual(expected, observed)


class TestImageSettings(_TestImagesBase):
    """Tests for ImageSettings class."""

    def test_csv_to_list(self):
        """Should parse the csv into a trimmed value list."""
        csv = 'start,end,  deviceid, begin group,end group  '
        expected = ['start', 'end', 'deviceid', 'begin group', 'end group']
        observed = ImageSettings._csv_to_list(csv)
        self.assertEqual(expected, observed)

    def test_locate_language_settings_columns(self):
        """Should return the column position and name of language settings."""
        expected = {2: {'language': 'english'}}
        sheet = self.xlsform1_workbook.sheet_by_name(
            sheet_name='image_settings')
        observed = ImageSettings._locate_language_settings_columns(
            image_settings_sheet=sheet)
        self.assertEqual(expected, observed)

    def test_read_language_settings_values(self):
        """Should return a dict with a key for all supported settings."""
        sheet = self.xlsform1_workbook.sheet_by_name(
            sheet_name='image_settings')
        settings = ImageSettings._read_language_settings_values(
            image_settings_sheet=sheet, column_index=2, settings=dict())
        expected = set(ImageSettings._supported_settings())
        observed = set(settings.keys()) | {'language'}
        self.assertEqual(expected, observed)

    def test_read_image_settings(self):
        """Should return expected sample settings values."""
        settings = ImageSettings.read(self.xlsform1_workbook)
        observed = settings.get(2)
        self.assertEqual(observed['language'], 'english')
        self.assertEqual(observed['text_label_font_name'], 'arialbd.ttf')
        self.assertIsInstance(observed['text_hint_pixels_line'], int)
        self.assertIsInstance(observed['nest_image_column'], str)

    def test_get_font_kwargs_label(self):
        """Should return label font kwargs dict with expected values."""
        settings = {
            'text_label_font_name': 'arialbd.ttf',
            'text_label_font_size': 32,
            'text_label_font_color': 'black'
        }
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='label')
        self.assertEqual('black', font_kwargs['font_color'])
        self.assertEqual('Arial', font_kwargs['font'].font.family)
        self.assertEqual('Bold', font_kwargs['font'].font.style)
        self.assertEqual(32, font_kwargs['font'].size)

    def test_get_font_kwargs_hint(self):
        """Should return hint font kwargs dict with expected values."""
        settings = {
            'text_hint_font_name': 'arial.ttf',
            'text_hint_font_size': 28,
            'text_hint_font_color': 'black'
        }
        font_kwargs = ImageSettings._get_font_kwargs(
            settings=settings, label_or_hint='hint')
        self.assertEqual('black', font_kwargs['font_color'])
        self.assertEqual('Arial', font_kwargs['font'].font.family)
        self.assertEqual('Regular', font_kwargs['font'].font.style)
        self.assertEqual(28, font_kwargs['font'].size)


class TestImageContent(_TestImagesBase):
    """Tests for ImageContent class."""

    def test_locate_image_content_columns(self):
        """Should return the column index of the image content columns."""
        expected = {'item_type': 0,
                    'file_name_column': 1,
                    'text_label_column': 2,
                    'text_hint_column': 3,
                    'nest_image_column': 4}
        settings = {2: {'language': 'english',
                        'file_name_column': 'name',
                        'text_label_column': 'label',
                        'text_hint_column': 'hint',
                        'nest_image_column': 'image'}}
        sheet = self.xlsform1_workbook.sheet_by_name(sheet_name='survey')
        observed = ImageContent._locate_image_content_columns(
            survey_sheet=sheet, settings_values=settings[2])
        self.assertEqual(expected, observed)

    def test_read_survey_image_content_values(self):
        """Should return content values with expected keys."""
        expected = {'item_type', 'file_name_column', 'text_label_column',
                    'text_hint_column', 'nest_image_column', }
        settings = {2: {'language': 'english',
                        'item_type': 'text',
                        'file_name_column': 'name',
                        'text_label_column': 'label',
                        'text_hint_column': 'hint',
                        'nest_image_column': 'image'}}
        sheet = self.xlsform1_workbook.sheet_by_name(sheet_name='survey')
        column_locations = ImageContent._locate_image_content_columns(
            survey_sheet=sheet, settings_values=settings[2])
        observed = ImageContent._read_survey_image_content_values(
            survey_sheet=sheet, column_locations=column_locations)
        self.assertEqual(expected, set(observed[0].keys()))

    def test_read_from_image_settings(self):
        """Should return expected sample image content values."""
        settings = ImageSettings.read(
            xlsform_workbook=self.xlsform1_workbook)
        observed = ImageContent.read(
            xlsform_workbook=self.xlsform1_workbook, settings=settings[2])
        image_content = observed['image_content']
        self.assertEqual('nl_visit', image_content[0]['file_name_column'])
        self.assertEqual(['Subject ID'], image_content[2]['text_label_column'])


class TestImageContentWrapText(TestCase):
    """Tests for ImageContent._wrap_text()"""

    def test_no_newline_greater_than_wrap_char(self):
        """Should return text broken on the wrap character amount."""
        text = 'This is some text with no internal punctuation.'
        wrap = int(len(text) / 2)
        expected = ['This is some text with', 'no internal', 'punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_no_newline_less_than_wrap_char(self):
        """Should return text as a list with no breaks."""
        text = 'This is some text with no internal punctuation.'
        wrap = int(len(text) + 1)
        expected = [text]
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_newline_greater_than_wrap_char(self):
        """Should return text broken at both wrap char and punctuation."""
        text = 'This is some text. It has internal punctuation.'
        wrap = int(len(text) / 3)
        expected = [
            'This is some', 'text.', ' ', 'It has', 'internal', 'punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_newline_less_than_wrap_char(self):
        """Should return text broken on the internal punctuation."""
        text = 'This is some text. It has internal punctuation.'
        wrap = int(len(text) + 1)
        expected = ['This is some text.', ' ', 'It has internal punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_empty_string(self):
        """Should return an empty list."""
        text = ''
        wrap = 10
        expected = []
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)
