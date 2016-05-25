import unittest
import os
import shutil
from unittest.mock import MagicMock, patch
from tkinter import messagebox
from odk_tools.gui.gui import ODKToolsGui as gui
from odk_tools.gui.gui import _CapturingHandler
import logging


class TestGui(unittest.TestCase):
    """Tests for functions in the GUI module."""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.path.dirname(__file__)
        cls.fixture_path_xform = os.path.join(cls.cwd, "R1309 BEHAVE.xml")
        cls.fixture_path_xlsform = os.path.join(cls.cwd, "Q1302_BEHAVE.xlsx")
        cls.fixture_path_xlsform_huge_fonts = os.path.join(
            cls.cwd, "R1309_BEHAVE_huge_fonts.xlsx")
        cls.fixture_path_sitelangs = os.path.join(
            cls.cwd, "site_languages.xlsx")
        cls.fixture_path_sitelangs_single = os.path.join(
            cls.cwd, "site_languages_single.xlsx")
        package_root = os.path.dirname(os.path.dirname(cls.cwd))
        bin_directory = os.path.join(os.path.dirname(package_root), "bin")
        cls.odk_validate_path = os.path.join(bin_directory, "ODK_Validate.jar")

    def setUp(self):
        self.remove_after_done_dir = ''
        self.remove_after_done_file = ''

    def tearDown(self):
        if self.remove_after_done_dir != '':
            shutil.rmtree(self.remove_after_done_dir, ignore_errors=True)
        if self.remove_after_done_file != '':
            os.remove(self.remove_after_done_file)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_is_java_callable_with_java_home_set(self):
        """Should locate java."""
        popen_kw = gui._popen_kwargs()
        popen_kw['env'] = {'JAVA_HOME': os.environ.get('JAVA_HOME')}
        observed, _ = gui._is_java_callable(popen_kwargs=popen_kw)
        self.assertTrue(observed)

    def test_is_java_callable_false_without_java_home(self):
        """Should fail to locate java."""
        popen_kw = gui._popen_kwargs()
        popen_kw['env'] = {}
        observed, _ = gui._is_java_callable(popen_kwargs=popen_kw)
        self.assertFalse(observed)

    def test_locate_odk_validate_in_context_dir(self):
        """Should return absolute path to ODK_Validate."""
        context = os.path.dirname(self.odk_validate_path)
        expected = self.odk_validate_path
        observed = gui._locate_odk_validate(context)
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
        validate_path = self.odk_validate_path
        java_path = ''
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
        validate_path = self.odk_validate_path
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
        with patch('tkinter.messagebox.showerror', MagicMock()) as msg_box:
            gui._validate_path(variable_name="XForm path", path='bananas')
        msg = "XForm path does not correspond to a file." + \
              "\nPlease check the path and try again."
        expected = {'title': 'File Error', 'message': msg}
        msg_box.assert_called_with(**expected)

    def test_validate_path_none_xform(self):
        """Should open an Input Error message box."""
        with patch('tkinter.messagebox.showerror', MagicMock()) as msg_box:
            gui._validate_path(variable_name="XForm path", path=None)
        msg = "XForm path is empty. Please either:\n- Enter the path, or" + \
              "\n- Select the path using the 'Browse...' button."
        expected = {'title': 'Input Error', 'message': msg}
        msg_box.assert_called_with(**expected)

    def test_run_generate_xform_all_valid_args(self):
        """Should return success run header message."""
        expected = "XLS2XForm was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        self.remove_after_done_file = xform_path
        observed, _ = gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        self.assertEqual(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_run_generate_xform_output_path_blank(self):
        """Should return success run header message."""
        expected = "XLS2XForm was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        self.remove_after_done_file = xform_path
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

    def test_run_generate_images_all_valid_args(self):
        """Should return success run header message."""
        expected = "Generate Images was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        patch_write = 'odk_tools.question_images.images.write_images'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_images(xlsform_path=xlsform_path)
        self.assertEqual(expected, header)

    def test_run_generate_images_invalid_xform(self):
        """Should return error header message."""
        expected = "Generate Images not run: invalid arguments."
        xlsform_path = 'not a valid path'
        messagebox.showerror = MagicMock()
        patch_write = 'odk_tools.question_images.images.write_images'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_images(xlsform_path=xlsform_path)
        self.assertEqual(expected, header)

    def test_run_generate_images_captures_logs(self):
        """Should have logs from generate images with oversized text."""
        xlsform_path = self.fixture_path_xlsform_huge_fonts
        class_path = 'odk_tools.question_images.images.Images.{0}'
        patch_save_path = class_path.format('_save_image')
        patch_dir_path = class_path.format('_create_output_directory')
        with patch(patch_save_path, MagicMock()):
            with patch(patch_dir_path, MagicMock(
                    return_value='my_xform-media')):
                _, content = gui._run_generate_images(
                    xlsform_path=xlsform_path)
        self.assertEqual(134, len(content))
        self.assertTrue(content[0].startswith("Text outside image margins."))

    def test_is_7zip_callable_with_installed(self):
        """Should locate 7zip."""
        popen_kw = gui._popen_kwargs()
        observed, _ = gui._is_7zip_callable(popen_kwargs=popen_kw)
        self.assertTrue(observed)

    def test_run_generate_editions_all_valid_args(self):
        """Should return success run header message."""
        expected = "Generate Editions was run. Output below."
        xform_path = self.fixture_path_xform
        sitelangs_path = self.fixture_path_sitelangs
        patch_write = 'odk_tools.language_editions.editions.write_editions'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                z7zip_path='')
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_xform(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = "not a valid path"
        sitelangs_path = self.fixture_path_sitelangs
        messagebox.showerror = MagicMock()
        patch_write = 'odk_tools.language_editions.editions.write_editions'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                z7zip_path='')
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_sitelangs(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = self.fixture_path_xform
        sitelangs_path = "not a valid path"
        messagebox.showerror = MagicMock()
        patch_write = 'odk_tools.language_editions.editions.write_editions'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                z7zip_path='')
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_7zip(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = self.fixture_path_xform
        sitelangs_path = self.fixture_path_sitelangs
        messagebox.showerror = MagicMock()
        patch_write = 'odk_tools.language_editions.editions.write_editions'
        with patch(patch_write, MagicMock()):
            header, _ = gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                z7zip_path='not a valid path')
        self.assertEqual(expected, header)

    def test_run_generate_editions_captures_logs(self):
        """Should have logs from generate editions."""
        self.remove_after_done_dir = os.path.join(self.cwd, "editions")
        sitelangs = self.fixture_path_sitelangs_single
        xform = self.fixture_path_xform
        _, content = gui._run_generate_editions(
            xform_path=xform, sitelangs_path=sitelangs)
        self.assertEqual(7, len(content))
        self.assertEqual(
            content[0],
            "Preparing files for site: 64001, languages: ['english']")


class TestCapturingHandler(unittest.TestCase):
    """Tests for the CapturingHandler class."""

    def test_capture_handler_output(self):
        """Should return list of log messages."""
        test_logger = logging.getLogger("my_test_logger")
        test_logger.setLevel("INFO")
        capture = _CapturingHandler(logger=test_logger)
        messages = ['first message', 'this is a second message']
        test_logger.warn(messages[0])
        test_logger.info(messages[1])
        test_logger.removeHandler(hdlr=capture)
        self.assertEqual(capture.watcher.output, messages)
