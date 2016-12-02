from odk_tools.gui.wrappers import validate_xform
from tests.gui import FixturePaths
import unittest
import os
from unittest.mock import MagicMock, patch


class TestValidateXForm(unittest.TestCase):

    def setUp(self):
        self.fixtures = FixturePaths()

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_is_java_callable_with_java_home_set(self):
        """Should locate java."""
        popen_kw = validate_xform.get_popen_kwargs()
        java_home = os.environ.get('JAVA_HOME')
        popen_kw['env'] = {'JAVA_HOME': java_home}
        observed = validate_xform._get_callable_java_path(popen_kwargs=popen_kw)
        self.assertTrue(observed.startswith(os.path.normpath(java_home)))

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_is_java_callable_false_with_java_home_removed(self):
        """Should fail to locate java."""
        popen_kw = validate_xform.get_popen_kwargs()
        java_home = os.environ.pop('JAVA_HOME')
        with self.assertRaises(ValueError):
            observed = validate_xform._get_callable_java_path(
                popen_kwargs=popen_kw)
            self.assertIn("Java does not appear to be callable", observed)
        os.environ['JAVA_HOME'] = java_home

    def test_locate_odk_validate(self):
        """Should return absolute path to ODK_Validate."""
        observed = validate_xform._locate_odk_validate()
        self.assertTrue(os.path.isfile(observed), msg=observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_all_valid_args(self):
        """Should return success run header message."""
        expected = "task was run"
        validate_path = validate_xform._locate_odk_validate()
        java_path = ''
        xform_path = self.fixtures.files["R1309 BEHAVE.xml"]
        patch_call = 'odk_tools.gui.wrappers.validate_xform._call_odk_validate'
        with patch(patch_call, MagicMock()):
            observed = validate_xform.wrapper(
                java_path=java_path, validate_path=validate_path,
                xform_path=xform_path)
            self.assertIn(expected, observed)

    @unittest.skipIf(os.environ.get('JAVA_HOME') is None, "JAVA_HOME not set.")
    def test_run_validate_invalid_args(self):
        """Should return output text indicating validate not run."""
        expected = 'task not run'
        observed = validate_xform.wrapper(
            java_path='spam', validate_path='eggs', xform_path='ham')
        self.assertIn(expected, observed)
