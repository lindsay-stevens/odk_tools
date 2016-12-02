from odk_tools.gui.wrappers import generate_images
from tests.gui import FixturePaths
import unittest
from unittest.mock import MagicMock, patch


class TestGenerateImages(unittest.TestCase):

    def setUp(self):
        self.fixtures = FixturePaths()

    def test_run_generate_images_all_valid_args(self):
        """Should return message indicating that the task was run."""
        expected = "task was run"
        xlsform_path = self.fixtures.files["Q1302_BEHAVE.xlsx"]
        patch_write = 'odk_tools.question_images.images.write_images'
        with patch(patch_write, MagicMock()):
            result = generate_images.wrapper(xlsform_path=xlsform_path)
        self.assertIn(expected, result)

    def test_run_generate_images_invalid_args(self):
        """Should return message indicating that the task was not run."""
        expected = "task not run"
        observed = generate_images.wrapper(xlsform_path="spam")
        self.assertIn(expected, observed)

    def test_run_generate_images_captures_logs(self):
        """Should have logs from generate images with oversized text."""
        xlsform_path = self.fixtures.files["R1309_BEHAVE_huge_fonts.xlsx"]
        class_path = 'odk_tools.question_images.images.Images.{0}'
        patch_save_path = class_path.format('_save_image')
        patch_dir_path = class_path.format('_create_output_directory')
        with patch(patch_save_path, MagicMock()):
            with patch(patch_dir_path, MagicMock(
                    return_value='my_xform-media')):
                observed = generate_images.wrapper(xlsform_path=xlsform_path)
        expected = "Text outside image margins."
        self.assertIn(expected, observed)
