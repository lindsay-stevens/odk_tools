import unittest
import os
from unittest.mock import MagicMock
from tkinter import messagebox
from odk_tools.gui.gui import ODKToolsGui as gui


class TestGui(unittest.TestCase):
    """Tests for functions in the GUI module."""

    @classmethod
    def setUpClass(cls):
        cwd = os.path.dirname(__file__)
        cls.fixture_path_xform = os.path.join(cwd, "R1309 BEHAVE.xml")
        cls.fixture_path_xlsform = os.path.join(cwd, "Q1302_BEHAVE.xlsx")

    def setUp(self):
        self.remove_after_done = None

    def tearDown(self):
        if self.remove_after_done is not None:
            os.remove(self.remove_after_done)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_is_java_callable_true_with_java_home_set(self):
        """Should locate java."""
        popen_kw = gui._popen_kwargs()
        popen_kw['env'] = {'JAVA_HOME': os.environ.get('JAVA_HOME')}
        observed, _ = gui._is_java_callable(popen_kwargs=gui._popen_kwargs())
        self.assertTrue(observed)

    def test_is_java_callable_false_without_java_home(self):
        """Should fail to locate java."""
        popen_kw = gui._popen_kwargs()
        popen_kw['env'] = {}
        observed, _ = gui._is_java_callable(popen_kwargs=popen_kw)
        self.assertFalse(observed)

    def test_locate_odk_validate_in_test_dir(self):
        """Should return absolute path to ODK_Validate."""
        current_directory = gui._current_directory()
        expected = os.path.join(current_directory, "ODK_Validate.jar")
        observed = gui._locate_odk_validate(current_directory)
        self.assertEqual(expected, observed)

    def test_locate_odk_validate(self):
        """Should return None."""
        current_directory = os.path.dirname(__file__)
        observed = gui._locate_odk_validate(current_directory)
        self.assertIsNone(observed)

    def test_popen_kwargs(self):
        """Should return expected key set."""
        expected = {'universal_newlines', 'cwd', 'stdin', 'stdout', 'stderr'}
        observed = gui._popen_kwargs().keys()
        self.assertEqual(expected, observed)

    def test_current_directory(self):
        """Should return the absolute path to gui.py"""
        expected = os.path.dirname(os.path.dirname(__file__))
        observed = gui._current_directory()
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_all_valid_args(self):
        """Should return success run header message."""
        expected = "Validate was run. Output below."
        java_path = ''
        validate_path = ''
        xform_path = self.fixture_path_xform
        observed, _ = gui._run_validate_xform(
            java_path=java_path, validate_path=validate_path,
            xform_path=xform_path)
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = 'Validate not run: invalid arguments.'
        messagebox.showerror = MagicMock()
        observed, _ = gui._run_validate_xform(
            java_path='', validate_path='', xform_path='')
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_java_specified(self):
        """Should return parsing result."""
        expected = "Parsing form..."
        found, java_path = gui._is_java_callable(gui._popen_kwargs())
        java_path = os.path.expandvars(java_path).replace('"', '')
        validate_path = ''
        xform_path = self.fixture_path_xform
        _, observed = gui._run_validate_xform(
            java_path=java_path, validate_path=validate_path,
            xform_path=xform_path)
        self.assertTrue(observed[1].startswith(expected))

    def test_validate_path_valid_xform(self):
        """Should open a File Error message box."""
        observed = gui._validate_path(
            variable_name="XForm path", path=self.fixture_path_xform)
        self.assertTrue(observed)

    def test_validate_path_blank_xform(self):
        """Should open a File Error message box."""
        msgbox = messagebox
        msgbox.showerror = MagicMock()
        gui._validate_path(variable_name="XForm path", path='bananas')
        msg = "XForm path does not correspond to a file." + \
              "\nPlease check the path and try again."
        expected = {'title': 'File Error', 'message': msg}
        msgbox.showerror.assert_called_with(**expected)

    def test_validate_path_none_xform(self):
        """Should open an Input Error message box."""
        msgbox = messagebox
        msgbox.showerror = MagicMock()
        gui._validate_path(variable_name="XForm path", path=None)
        msg = "XForm path is empty. Please either:\n- Enter the path, or" + \
              "\n- Select the path using the 'Browse...' button."
        expected = {'title': 'Input Error', 'message': msg}
        msgbox.showerror.assert_called_with(**expected)

    def test_run_generate_xform_all_valid_args(self):
        """Should return success run header message."""
        expected = "XLS2XForm was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        self.remove_after_done = xform_path
        observed, _ = gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        self.assertEqual(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_run_generate_xform_output_path_blank(self):
        """Should return success run header message."""
        expected = "XLS2XForm was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        self.remove_after_done = xform_path
        observed, _ = gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path='')
        self.assertEqual(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_run_generate_xform_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = "XLS2XForm not run: invalid arguments."
        messagebox.showerror = MagicMock()
        observed, _ = gui._run_generate_xform(
            xlsform_path='', xform_path='')
        self.assertEqual(expected, observed)

    def test_get_same_xlsform_name(self):
        """Should return a path in the same place as input file."""
        xlsform_path = self.fixture_path_xlsform
        expected = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        observed = gui._get_same_xlsform_name(xlsform_path=xlsform_path)
        self.assertEqual(expected, observed)