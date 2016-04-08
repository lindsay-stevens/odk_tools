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

    def test_read_image_settings_parses_csv(self):
        """Should parse the csv into a trimmed value list."""
        csv = 'start,end,  deviceid, begin group,end group  '
        expected = ['start', 'end', 'deviceid', 'begin group', 'end group']
        settings = self.images._read_image_settings(self.xlsform1_workbook)
        observed = settings[2]['type_ignore_list']
        self.assertEqual(expected, observed)

    def test_read_image_settings(self):
        """Should return the expected quantity of and sample values."""
        settings = self.images._read_image_settings(self.xlsform1_workbook)
        observed = settings.get(2)
        self.assertIsNotNone(observed)
        self.assertEqual(observed['language'], 'english')
        self.assertEqual(observed['text_label_font_name'], 'arialbd.ttf')
        self.assertEqual(26, len(observed.keys()))

    def test_read_survey_values(self):
        """Should return the expected quantity of and sample values."""
        pass
