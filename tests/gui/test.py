import unittest
import os
import shutil
from unittest.mock import MagicMock, patch
from tkinter import messagebox
import odk_tools
from odk_tools.gui.gui import ODKToolsGui as Gui
from odk_tools.gui.gui import _CapturingHandler
import logging
import xmltodict


class TestGui(unittest.TestCase):
    """Tests for functions in the GUI module."""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.path.dirname(__file__)
        cls.fixture_path_xform = os.path.join(cls.cwd, "R1309 BEHAVE.xml")
        cls.fixture_path_xlsform = os.path.join(cls.cwd, "Q1302_BEHAVE.xlsx")
        cls.fixture_path_xlsform_1405 = os.path.join(
            cls.cwd, "R1405_BEHAVE.xlsx")
        cls.fixture_path_xlsform_broken = os.path.join(
            cls.cwd, "Q1302_BEHAVE_broken.xlsx")
        cls.fixture_path_xlsform_huge_fonts = os.path.join(
            cls.cwd, "R1309_BEHAVE_huge_fonts.xlsx")
        cls.fixture_path_sitelangs = os.path.join(
            cls.cwd, "site_languages.xlsx")
        cls.fixture_path_sitelangs_single = os.path.join(
            cls.cwd, "site_languages_single.xlsx")
        cls.package_root = os.path.dirname(os.path.dirname(cls.cwd))
        bin_directory = os.path.join(cls.package_root, "bin")
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
        popen_kw = Gui._popen_kwargs()
        popen_kw['env'] = {'JAVA_HOME': os.environ.get('JAVA_HOME')}
        observed, _ = Gui._is_java_callable(popen_kwargs=popen_kw)
        self.assertTrue(observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_is_java_callable_false_with_java_home_removed(self):
        """Should fail to locate java."""
        popen_kw = Gui._popen_kwargs()
        java_home = os.environ.pop('JAVA_HOME')
        observed, _ = Gui._is_java_callable(popen_kwargs=popen_kw)
        os.environ['JAVA_HOME'] = java_home
        self.assertFalse(observed)

    def test_locate_odk_validate_in_context_dir(self):
        """Should return absolute path to ODK_Validate."""
        context = os.path.dirname(self.odk_validate_path)
        expected = self.odk_validate_path
        observed = Gui._locate_odk_validate(context)
        self.assertEqual(expected, observed)

    def test_locate_odk_validate(self):
        """Should return None."""
        current_directory = os.path.dirname(__file__)
        observed = Gui._locate_odk_validate(current_directory)
        self.assertIsNone(observed)

    def test_popen_kwargs(self):
        """Should return expected key set."""
        expected = {'universal_newlines', 'cwd', 'stdin', 'stdout', 'stderr'}
        observed = Gui._popen_kwargs().keys()
        self.assertEqual(expected, observed)

    def test_current_directory(self):
        """Should return the absolute path to gui.py"""
        expected = os.path.dirname(odk_tools.gui.gui.__file__)
        observed = Gui._current_directory()
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_all_valid_args(self):
        """Should return success run header message."""
        expected = "Validate was run. Output below."
        validate_path = self.odk_validate_path
        java_path = ''
        xform_path = self.fixture_path_xform
        observed, _ = Gui._run_validate_xform(
            java_path=java_path, validate_path=validate_path,
            xform_path=xform_path)
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = 'Validate not run: invalid arguments.'
        messagebox.showerror = MagicMock()
        observed, _ = Gui._run_validate_xform(
            java_path='', validate_path='', xform_path='')
        self.assertEqual(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_java_specified(self):
        """Should return parsing result."""
        expected = "Parsing form..."
        found, java_path = Gui._is_java_callable(Gui._popen_kwargs())
        java_path = os.path.expandvars(java_path).replace('"', '')
        validate_path = self.odk_validate_path
        xform_path = self.fixture_path_xform
        _, observed = Gui._run_validate_xform(
            java_path=java_path, validate_path=validate_path,
            xform_path=xform_path)
        self.assertTrue(observed[1].startswith(expected))

    def test_validate_path_valid_xform(self):
        """Should open a File Error message box."""
        observed = Gui._validate_path(
            variable_name="XForm path", path=self.fixture_path_xform)
        self.assertTrue(observed)

    def test_validate_path_blank_xform(self):
        """Should open a File Error message box."""
        with patch('tkinter.messagebox.showerror', MagicMock()) as msg_box:
            Gui._validate_path(variable_name="XForm path", path='bananas')
        msg = "XForm path does not correspond to a file." + \
              "\nPlease check the path and try again."
        expected = {'title': 'File Error', 'message': msg}
        msg_box.assert_called_with(**expected)

    def test_validate_path_none_xform(self):
        """Should open an Input Error message box."""
        with patch('tkinter.messagebox.showerror', MagicMock()) as msg_box:
            Gui._validate_path(variable_name="XForm path", path=None)
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
        observed, _ = Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        self.assertEqual(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_run_generate_xform_all_valid_args_broken_xform(self):
        """Should return error messages from the xslx form converter."""
        expected = ["[row : 16] List name not in choices sheet: "
                    "a_list_that_doesnt_exist"]
        xlsform_path = self.fixture_path_xlsform_broken
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        _, observed = Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        self.assertListEqual(expected, observed)

    def test_run_generate_xform_output_path_blank(self):
        """Should return success run header message."""
        expected = "XLS2XForm was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        xform_path = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        self.remove_after_done_file = xform_path
        observed, _ = Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path='')
        self.assertEqual(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_run_generate_xform_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = "XLS2XForm not run: invalid arguments."
        messagebox.showerror = MagicMock()
        observed, _ = Gui._run_generate_xform(
            xlsform_path='', xform_path='')
        self.assertEqual(expected, observed)

    def test_get_same_xlsform_name(self):
        """Should return a path in the same place as input file."""
        xlsform_path = self.fixture_path_xlsform
        expected = self.fixture_path_xlsform.replace(".xlsx", ".xml")
        observed = Gui._get_same_xlsform_name(xlsform_path=xlsform_path)
        self.assertEqual(expected, observed)

    def test_run_generate_images_all_valid_args(self):
        """Should return success run header message."""
        expected = "Generate Images was run. Output below."
        xlsform_path = self.fixture_path_xlsform
        patch_write = 'odk_tools.question_images.images.write_images'
        with patch(patch_write, MagicMock()):
            header, _ = Gui._run_generate_images(xlsform_path=xlsform_path)
        self.assertEqual(expected, header)

    def test_run_generate_images_invalid_xform(self):
        """Should return error header message."""
        expected = "Generate Images not run: invalid arguments."
        xlsform_path = 'not a valid path'
        messagebox.showerror = MagicMock()
        patch_write = 'odk_tools.question_images.images.write_images'
        with patch(patch_write, MagicMock()):
            header, _ = Gui._run_generate_images(xlsform_path=xlsform_path)
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
                _, content = Gui._run_generate_images(
                    xlsform_path=xlsform_path)
        self.assertEqual(134, len(content))
        self.assertTrue(content[0].startswith("Text outside image margins."))

    def test_run_generate_editions_all_valid_args(self):
        """Should return success run header message."""
        expected = "Generate Editions was run. Output below."
        xform_path = self.fixture_path_xform
        sitelangs_path = self.fixture_path_sitelangs
        patch_run = 'odk_tools.language_editions.' \
                    'editions.Editions._run_zip_jobs'
        with patch(patch_run, MagicMock()):
            header, _ = Gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_xform(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = "not a valid path"
        sitelangs_path = self.fixture_path_sitelangs
        messagebox.showerror = MagicMock()
        patch_run = 'odk_tools.language_editions.' \
                    'editions.Editions._run_zip_jobs'
        with patch(patch_run, MagicMock()):
            header, _ = Gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_sitelangs(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = self.fixture_path_xform
        sitelangs_path = "not a valid path"
        messagebox.showerror = MagicMock()
        patch_run = 'odk_tools.language_editions.' \
                    'editions.Editions._run_zip_jobs'
        with patch(patch_run, MagicMock()):
            header, _ = Gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
        self.assertEqual(expected, header)

    def test_run_generate_editions_invalid_collect_settings(self):
        """Should return error header message."""
        expected = "Generate Editions not run: invalid arguments."
        xform_path = self.fixture_path_xform
        sitelangs_path = self.fixture_path_sitelangs
        messagebox.showerror = MagicMock()
        patch_run = 'odk_tools.language_editions.' \
                    'editions.Editions._run_zip_jobs'
        with patch(patch_run, MagicMock()):
            header, _ = Gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings="doesn't exist")
        self.assertEqual(expected, header)

    def test_run_generate_editions_captures_logs(self):
        """Should have logs from generate editions."""
        xform_path = self.fixture_path_xform
        sitelangs_path = self.fixture_path_sitelangs_single
        patch_run = 'odk_tools.language_editions.' \
                    'editions.Editions._run_zip_jobs'
        with patch(patch_run, MagicMock()):
            _, content = Gui._run_generate_editions(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
        self.assertEqual(5, len(content), msg=content)
        self.assertEqual(
            content[0],
            "Preparing files for site: 64001, languages: ('english',)")

    @staticmethod
    def get_temp_patch_content_xml_template():
        return """<?xml version="1.0" encoding="utf-8"?>
            <h:html>
                <h:head>
                    <model>
                        <bind nodeset="/MYFORM/a/item1"></bind>
                        <itext>
                            <translation>
                                <text id="/MYFORM/a/item1:label">
                                    <value form="image">my_image1.jpg</value>{0}
                                </text>
                            </translation>
                        </itext>
                    </model>
                </h:head>
            </h:html>"""

    def test_xform_empty_question_label_patch_content_add(self):
        """Should add a blank value in the text node where one doesn"t exist."""
        xml_template = self.get_temp_patch_content_xml_template()
        expected = "&nbsp;"
        xml_input = xml_template.format("")
        parsed, _ = Gui._xform_empty_question_label_patch_content(xml_input)
        itext = parsed["h:html"]["h:head"]["model"]["itext"]
        observed = itext["translation"][0]["text"][0]["value"]
        self.assertIn(expected, observed)

    def test_xform_empty_question_label_patch_content_no_overwrite(self):
        """Should not overwrite plain text itext values that already exist."""
        xml_template = self.get_temp_patch_content_xml_template()
        expected = "My plain string itext question label"
        xml_input = xml_template.format(
            """<value>{0}</value>""".format(expected))
        observed, _ = Gui._xform_empty_question_label_patch_content(xml_input)
        parsed, _ = Gui._xform_empty_question_label_patch_content(xml_input)
        itext = parsed["h:html"]["h:head"]["model"]["itext"]
        observed = itext["translation"][0]["text"][0]["value"][1]["#text"]
        self.assertEqual(expected, observed)

    def test_xform_empty_question_label_patch_from_usual_call_path(self):
        """Should replace the standard result with a patched XML XForm file."""
        expected = "Added itext value patch (&nbsp; fix)."
        xlsform_path = os.path.join(self.cwd, "empty_question_label_patch.xlsx")
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.remove_after_done_file = xform_path
        _, observed = Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        self.assertIn(expected, observed)
        self.assertTrue(os.path.isfile(xform_path))

    def test_xform_empty_question_label_patch_with_full_xlsform(self):
        """Should insert patch values to all text value elements."""
        xlsform_path = self.fixture_path_xlsform
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.remove_after_done_file = xform_path
        Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        with open(xform_path, mode="r") as xform_file:
            xform_content = xform_file.read()
        parsed = xmltodict.parse(xform_content, force_list=("value",))
        trans = parsed["h:html"]["h:head"]["model"]["itext"]["translation"]
        for text in trans["text"]:
            text_value_count = len(text["value"])
            text_value = text["value"]
            if "&nbsp;" in text_value or \
                    any(isinstance(x, str) for x in text_value) or \
                    text.get("form") in ["short", "long"]:
                pass
            else:
                fail_msg = "Could not find &nbsp; or plain text value in " \
                           " text/@id: {0} ".format(text["@id"])
                self.fail(fail_msg)
            if text_value_count > 2:
                fail_msg = "Maximum of 2 translation text values expected. \n" \
                           "Found {0} values for text/@id: {1} ".format(
                               text_value_count, text["@id"])
                self.fail(fail_msg)

    def test_xform_empty_question_label_patch_validates_ok(self):
        """Should pass validate step without errors."""
        xlsform_path = self.fixture_path_xlsform
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.remove_after_done_file = xform_path
        Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        _, observed = Gui._run_validate_xform(
            java_path='', validate_path=self.odk_validate_path,
            xform_path=xform_path)
        if isinstance(observed, list):
            observed = "".join(observed)
        expected = "Xform is valid"
        self.assertIn(expected, observed)

    def test_xform_empty_question_label_patch_validates_ok_unicode(self):
        """Should pass validate step without errors."""
        xlsform_path = self.fixture_path_xlsform_1405
        # 1405 includes a whole lot of unicode characters.
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.remove_after_done_file = xform_path
        Gui._run_generate_xform(
            xlsform_path=xlsform_path, xform_path=xform_path)
        _, observed = Gui._run_validate_xform(
            java_path='', validate_path=self.odk_validate_path,
            xform_path=xform_path)
        if isinstance(observed, list):
            observed = "".join(observed)
        expected = "Xform is valid"
        self.assertIn(expected, observed)


class TestCapturingHandler(unittest.TestCase):
    """Tests for the CapturingHandler class."""

    def test_capture_handler_output(self):
        """Should return list of log messages."""
        test_logger = logging.getLogger("my_test_logger")
        test_logger.setLevel("INFO")
        capture = _CapturingHandler(logger=test_logger)
        messages = ["first message", "this is a second message"]
        test_logger.warning(messages[0])
        test_logger.info(messages[1])
        test_logger.removeHandler(hdlr=capture)
        self.assertEqual(capture.watcher.output, messages)
