import os
import unittest
from odk_tools.gui import utils


class TestUtils(unittest.TestCase):

    def test_not_empty_with_empty(self):
        variable_name = "my_var"
        path = ""
        valid, msg = utils.not_empty(variable_name=variable_name, path=path)
        self.assertFalse(valid)
        self.assertIn(variable_name, msg)
        self.assertIn("is empty", msg)

    def test_not_empty_with_not_empty(self):
        variable_name = "my_var"
        path = "C:/some/path"
        valid, msg = utils.not_empty(variable_name=variable_name, path=path)
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_file_exists_with_no_file(self):
        variable_name = "my_var"
        path = os.path.join(os.path.dirname(__file__), "doesnt_exist.jpg")
        valid, msg = utils.file_exists(variable_name=variable_name, path=path)
        self.assertFalse(valid)
        self.assertIn(variable_name, msg)
        self.assertIn("does not correspond to a file", msg)

    def test_file_exists_with_file(self):
        variable_name = "my_var"
        path = os.path.abspath(__file__)
        valid, msg = utils.file_exists(variable_name=variable_name, path=path)
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_file_extension_matches_with_no_match(self):
        variable_name = "my_var"
        path = os.path.join(os.path.dirname(__file__), "a_file.jpg")
        valid, msg = utils.file_extension_matches(
            variable_name=variable_name, path=path, file_extension=".xml")
        self.assertFalse(valid)
        self.assertIn(variable_name, msg)
        self.assertIn("Required extension", msg)

    def test_file_extension_matches_with_no_extension(self):
        variable_name = "my_var"
        path = os.path.join(os.path.dirname(__file__), "a_file")
        valid, msg = utils.file_extension_matches(
            variable_name=variable_name, path=path, file_extension=".jpg")
        self.assertFalse(valid)
        self.assertIn(variable_name, msg)

    def test_file_extension_matches_with_match(self):
        variable_name = "my_var"
        path = os.path.join(os.path.dirname(__file__), "a_file.jpg")
        valid, msg = utils.file_extension_matches(
            variable_name=variable_name, path=path, file_extension=".jpg")
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_clean_path_with_none(self):
        self.assertEqual("", utils.clean_path(path=None))

    def test_clean_path_with_invalid_wrapping_characters(self):
        expected = os.path.abspath(__file__)
        test_path = '\t \r"{0}\n"'.format(expected)
        observed = utils.clean_path(path=test_path)
        self.assertEqual(expected, observed)

    def test_validate_path_raises_for_bad_path(self):
        variable_name = "my_var"
        test_path = ""
        with self.assertRaises(ValueError) as ve:
            utils.validate_path(variable_name=variable_name,
                                path=test_path, file_extension=".xml")
            self.assertIn("is empty", ve.msg)

    def test_validate_path_returns_for_valid_path(self):
        variable_name = "my_var"
        test_path = os.path.abspath(__file__)
        observed = utils.validate_path(variable_name=variable_name,
                                       path=test_path, file_extension=".py")
        self.assertEqual(test_path, observed)

    def test_format_output_with_content_string(self):
        header = "Something happened!"
        content = "And it was mysterious."
        expected = len(header) + 2 + len(content)
        observed = len(utils.format_output(header=header, content=content))
        self.assertEqual(expected, observed)

    def test_format_output_with_content_list(self):
        header = "Something happened!"
        content = ["And it was mysterious.", "And it was scary."]
        expected = len(header) + 2 + len(content[0]) + 2 + len(content[1])
        observed = len(utils.format_output(header=header, content=content))
        self.assertEqual(expected, observed)
