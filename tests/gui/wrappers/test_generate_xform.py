from odk_tools.gui.wrappers import generate_xform
from tests.gui import FixturePaths
import unittest
from unittest.mock import MagicMock, patch
import os


class TestGenerateXForm(unittest.TestCase):

    def setUp(self):
        self.fixtures = FixturePaths()
        self.clean_up_file = None

    def tearDown(self):
        if self.clean_up_file is not None:
            os.remove(self.clean_up_file)

    def test_run_generate_xform_all_valid_args(self):
        """Should return message indicating that the task was run."""
        expected = "task was run"
        xlsform_path = self.fixtures.files["Q1302_BEHAVE.xlsx"]
        patch_convert = 'pyxform.xls2xform.xls2xform_convert'
        with patch(patch_convert, MagicMock()):
            observed = generate_xform.wrapper(xlsform_path=xlsform_path)[0]
        self.assertIn(expected, observed)

    def test_run_generate_xform_all_valid_args_broken_xform(self):
        """Should return error messages from the xslx form converter."""
        expected = ["[row : 16] List name not in choices sheet: ",
                    "a_list_that_doesnt_exist"]
        xlsform_path = self.fixtures.files["Q1302_BEHAVE_broken.xlsx"]
        xform_path = xlsform_path.replace("_broken.xlsx", ".xml")
        self.clean_up_file = xform_path
        observed = generate_xform.wrapper(xlsform_path=xlsform_path)[0]
        for message in expected:
            self.assertIn(message, observed)

    def test_run_generate_xform_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = "task not run"
        observed = generate_xform.wrapper(xlsform_path='spam')[0]
        self.assertIn(expected, observed)

