import os
import shutil
import xlrd
from unittest import TestCase
from odk_tools.question_images import images


class TestImages(TestCase):

    def setUp(self):
        self.xlsform1 = 'Q1302_BEHAVE.xlsx'
        self.xlsform1_workbook = xlrd.open_workbook(filename=self.xlsform1)
        self.test_output_path = None
        self.images = images.Images()

    def tearDown(self):
        if self.test_output_path is not None:
            shutil.rmtree(self.test_output_path, ignore_errors=True)

    def test_output_count(self):
        """Should create the expected number of images."""
        self.test_output_path = 'Q1302_BEHAVE-media'
        input_xlsx = self.xlsform1
        out_path = self.images._create_output_directory(input_xlsx)
        images.read_xlsform(out_path, input_xlsx)
        output_files = os.listdir(self.test_output_path)
        self.assertEqual(184, len(output_files))

    def test_create_output_directory(self):
        """Should create a folder with the expected name."""
        self.test_output_path = 'Q1302_BEHAVE-media'
        self.assertFalse(os.path.isdir(self.test_output_path))
        self.images._create_output_directory(self.xlsform1)
        self.assertTrue(os.path.isdir(self.test_output_path))

    def test_csv_to_list(self):
        """Should parse the csv into a trimmed value list."""
        csv = 'start,end,  deviceid, begin group,end group  '
        expected = ['start', 'end', 'deviceid', 'begin group', 'end group']
        observed = self.images._csv_to_list(csv)
        self.assertEqual(expected, observed)

    def test_locate_language_settings_columns(self):
        """Should return the column position and name of language settings."""
        expected = {2: {'language': 'english'}}
        sheet = self.xlsform1_workbook.sheet_by_name(
            sheet_name='image_settings')
        observed = self.images._locate_language_settings_columns(
            image_settings_sheet=sheet)
        self.assertEqual(expected, observed)

    def test_read_language_settings_values(self):
        """Should return a dict with a key for all supported settings."""
        sheet = self.xlsform1_workbook.sheet_by_name(
            sheet_name='image_settings')
        settings = self.images._read_language_settings_values(
            image_settings_sheet=sheet, column_index=2, settings=dict())
        expected = set(self.images._supported_settings())
        observed = set(settings.keys()) | {'language'}
        self.assertEqual(expected, observed)

    def test_read_image_settings(self):
        """Should return expected sample settings values."""
        settings = self.images._read_image_settings(self.xlsform1_workbook)
        observed = settings.get(2)
        self.assertEqual(observed['language'], 'english')
        self.assertEqual(observed['text_label_font_name'], 'arialbd.ttf')

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
        observed = self.images._locate_image_content_columns(
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
        column_locations = self.images._locate_image_content_columns(
            survey_sheet=sheet, settings_values=settings[2])
        observed = self.images._read_survey_image_content_values(
            survey_sheet=sheet, column_locations=column_locations)
        self.assertEqual(expected, set(observed[0].keys()))

    def test_read_survey_image_content(self):
        """Should return expected sample image content values."""
        settings = self.images._read_image_settings(
            xlsform_workbook=self.xlsform1_workbook)
        observed = self.images._read_survey_image_content(
            xlsform_workbook=self.xlsform1_workbook, settings=settings[2])
        image_content = observed['image_content']
        self.assertEqual('visit', image_content[0]['file_name_column'])
        self.assertEqual(['Subject ID'], image_content[3]['text_label_column'])
