import unittest
import os
from unittest.mock import MagicMock
from tkinter import messagebox
from odk_tools.gui.gui import ODKToolsGui as gui


class TestGui(unittest.TestCase):
    """Tests for functions in the GUI module."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_path_xform = os.path.join(
            os.path.dirname(__file__), 'R1309 BEHAVE.xml')

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

    def test_run_validate_all_valid_args(self):
        """Should return parsing result."""
        expected = "\nParsing form..."
        java_path = ''
        validate_path = ''
        xform_path = self.fixture_path_xform
        observed = gui._run_validate(java_path=java_path,
                                     validate_path=validate_path,
                                     xform_path=xform_path)
        self.assertTrue(observed.startswith(expected))

    def test_run_validate_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = 'Validate not run: invalid arguments.\n'
        messagebox.showerror = MagicMock()
        observed = gui._run_validate(java_path='',
                                     validate_path='',
                                     xform_path='')
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_java_specified(self):
        """Should return parsing result."""
        expected = "\nParsing form..."
        found, java_path = gui._is_java_callable(gui._popen_kwargs())
        java_path = os.path.expandvars(java_path).replace('"', '')
        validate_path = ''
        xform_path = self.fixture_path_xform
        observed = gui._run_validate(java_path=java_path,
                                     validate_path=validate_path,
                                     xform_path=xform_path)
        self.assertTrue(observed.startswith(expected))

    def test_validate_path_valid_xform(self):
        """Should open a File Error message box."""
        observed = gui._validate_path(
            variable_name="XForm path", path=self.fixture_path_xform)
        self.assertTrue(observed)

    def test_validate_path_blank_xform(self):
        """Should open a File Error message box."""
        msgbox = messagebox
        msgbox.showerror = MagicMock()
        gui._validate_path(variable_name="XForm path", path='')
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
