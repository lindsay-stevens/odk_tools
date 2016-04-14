import os
import shutil
import xlrd
from unittest import TestCase
from odk_tools.question_images.images import Images, ImageContent, ImageSettings, read_xlsform


class _TestImagesBase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.xlsform1 = 'Q1302_BEHAVE.xlsx'
        cls.test_output_folder = 'Q1302_BEHAVE-media'
        cls.xlsform1_workbook = xlrd.open_workbook(filename=cls.xlsform1)

    def setUp(self):
        self.clean_test_output_folder = False
        self.images = Images()

    def tearDown(self):
        if self.clean_test_output_folder:
            shutil.rmtree(self.test_output_folder, ignore_errors=True)


class TestImages(_TestImagesBase):

    def test_output_count(self):
        """Should create the expected number of images."""
        self.clean_test_output_folder = True
        out_path = Images._create_output_directory(self.xlsform1)
        read_xlsform(out_path, self.xlsform1)
        output_files = os.listdir(self.test_output_folder)
        self.assertEqual(184, len(output_files))

    def test_create_output_directory(self):
        """Should create a folder with the expected name."""
        self.clean_test_output_folder = True
        shutil.rmtree(self.test_output_folder, ignore_errors=True)
        self.assertFalse(os.path.isdir(self.test_output_folder))
        Images._create_output_directory(self.xlsform1)
        self.assertTrue(os.path.isdir(self.test_output_folder))

    def test_create_base_image(self):
        """Should create an image of the expected size and colour."""
        observed = Images._create_base_image(50, 10, 'lavender')
        self.assertEqual((50, 10), observed[0].size)
        self.assertEqual((230, 230, 250), observed[0].load()[5, 5])

    def test_write(self):
        """WIP: expand to method tests"""
        #self.clean_test_output_folder = True
        settings = ImageSettings.read(
            xlsform_workbook=self.xlsform1_workbook)
        add_content = ImageContent.read(
            xlsform_workbook=self.xlsform1_workbook, settings=settings[2])
        observed = Images.write(self.xlsform1, add_content)
        print('h')


class TestImagesPaste(TestCase):

    def test_paste_image_shrink_tall_to_max_height(self):
        """Should resize to max_height."""
        base_image, pixels_from_top = Images._create_base_image(500, 500, 'red')
        paste_image, _ = Images._create_base_image(750, 600, 'blue')
        pixels_before = 5
        max_height = 40
        expected = 45
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=max_height)
        self.assertEqual(expected, observed)

    def test_paste_image_shrink_tall_to_max_height_with_y_offset(self):
        """Should resize to max_height."""
        base_image, _ = Images._create_base_image(500, 500, 'red')
        pixels_from_top = 100
        paste_image, _ = Images._create_base_image(750, 600, 'blue')
        pixels_before = 5
        max_height = 250
        expected = 355
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=max_height)
        self.assertEqual(expected, observed)

    def test_paste_image_shrink_wide_to_available(self):
        """Should resize to width."""
        base_image, pixels_from_top = Images._create_base_image(500, 500, 'red')
        paste_image, _ = Images._create_base_image(750, 600, 'blue')
        pixels_before = 5
        expected = 389
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_paste_image_shrink_tall_to_available(self):
        """Should resize to height."""
        base_image, pixels_from_top = Images._create_base_image(500, 500, 'red')
        paste_image, _ = Images._create_base_image(600, 750, 'blue')
        pixels_before = 5
        expected = 490
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_paste_image_shrink_square_to_available(self):
        """Should resize to width."""
        base_image, pixels_from_top = Images._create_base_image(500, 500, 'red')
        paste_image, _ = Images._create_base_image(600, 600, 'blue')
        pixels_before = 5
        expected = 485
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_paste_image_shrink_square_to_available_with_y_offset(self):
        """Should resize to fit available space."""
        base_image, _ = Images._create_base_image(500, 500, 'red')
        pixels_from_top = 50
        paste_image, _ = Images._create_base_image(600, 600, 'blue')
        pixels_before = 5
        expected = 490
        base_image, observed = Images._paste_image(
            base_image=base_image, pixels_from_top=pixels_from_top,
            paste_image=paste_image, pixels_before=pixels_before,
            max_height=None)
        self.assertEqual(expected, observed)

    def test_paste_image_doesnt_alter_input_paste_image(self):
        """Resizing should be done on a copy, not the original."""
        base_image, _ = Images._create_base_image(500, 500, 'red')
        paste_image, _ = Images._create_base_image(600, 600, 'blue')
        expected = (600, 600)
        Images._paste_image(
            base_image=base_image, pixels_from_top=20,
            paste_image=paste_image, pixels_before=20, max_height=50)
        observed = paste_image.size
        self.assertEqual(expected, observed)


class TestImageSettings(_TestImagesBase):

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


class TestImageContent(_TestImagesBase):

    def test_locate_image_content_columns(self):
        """Should return the column index of the image content columns."""
        expected = {'file_name_column': 1,
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
        expected = {'file_name_column', 'text_label_column',
                    'text_hint_column', 'nest_image_column'}
        settings = {2: {'language': 'english',
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
        self.assertEqual('visit', image_content[0]['file_name_column'])
        self.assertEqual(['Subject ID'], image_content[3]['text_label_column'])

    def test_wrap_text_no_newline_greater_than_wrap_char(self):
        """Should return text broken on the wrap character amount."""
        text = 'This is some text with no internal punctuation.'
        wrap = int(len(text) / 2)
        expected = ['This is some text with', 'no internal', 'punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_wrap_text_no_newline_less_than_wrap_char(self):
        """Should return text as a list with no breaks."""
        text = 'This is some text with no internal punctuation.'
        wrap = int(len(text) + 1)
        expected = [text]
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_wrap_text_with_newline_greater_than_wrap_char(self):
        """Should return text broken at both wrap char and punctuation."""
        text = 'This is some text. It has internal punctuation.'
        wrap = int(len(text) / 3)
        expected = [
            'This is some', 'text.', ' ', 'It has', 'internal', 'punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_wrap_text_with_newline_less_than_wrap_char(self):
        """Should return text broken on the internal punctuation."""
        text = 'This is some text. It has internal punctuation.'
        wrap = int(len(text) + 1)
        expected = ['This is some text.', ' ', 'It has internal punctuation.']
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)

    def test_wrap_text_with_empty_string(self):
        """Should return an empty list."""
        text = ''
        wrap = 10
        expected = []
        observed = ImageContent._wrap_text(text=text, wrap_characters=wrap)
        self.assertEqual(expected, observed)
