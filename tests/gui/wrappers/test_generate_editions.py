from odk_tools.gui.wrappers import generate_editions
from tests.gui import FixturePaths
import unittest
from unittest.mock import MagicMock, patch


class TestGenerateEditions(unittest.TestCase):

    def setUp(self):
        self.fixtures = FixturePaths()

    def test_run_generate_editions_all_valid_args(self):
        """Should return message indicating that the task was run."""
        expected = "task was run"
        xform_path = self.fixtures.files["R1309 BEHAVE.xml"]
        sitelangs_path = self.fixtures.files["site_languages.xlsx"]
        collect_settings = self.fixtures.files["collect.settings"]
        patch_run = "odk_tools.language_editions." \
                    "editions.Editions.write_language_editions"
        with patch(patch_run, MagicMock()):
            observed = generate_editions.wrapper(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
            observed_nest = generate_editions.wrapper(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=1, collect_settings=collect_settings)
        self.assertIn(expected, observed)
        self.assertIn(expected, observed_nest)

    def test_run_generate_editions_invalid_args(self):
        """Should return message indicating that the task was not run."""
        expected = "task not run"
        observed = generate_editions.wrapper(
            xform_path="spam", sitelangs_path="eggs", nest_in_odk_folders=0)
        self.assertIn(expected, observed)

    def test_run_generate_editions_captures_logs(self):
        """Should return message with captured logs from generate editions."""
        xform_path = self.fixtures.files["R1309 BEHAVE.xml"]
        sitelangs_path = self.fixtures.files["site_languages.xlsx"]
        patch_run = "odk_tools.language_editions." \
                    "editions.Editions._run_zip_jobs"
        with patch(patch_run, MagicMock()):
            observed = generate_editions.wrapper(
                xform_path=xform_path, sitelangs_path=sitelangs_path,
                nest_in_odk_folders=0, collect_settings=None)
        expected = "Preparing files for site: 64001, languages: ('english',)"
        self.assertIn(expected, observed)
