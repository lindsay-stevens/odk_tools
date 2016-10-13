import unittest
import os
import shutil
import zipfile
from lxml import etree
from odk_tools.language_editions.editions import Editions, _create_parser
import contextlib
import io
import warnings


class TestEditionsBase(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(__file__)
        self.xform1 = os.path.join(self.cwd, 'Q1309_BEHAVE.xml')
        self.document1 = etree.parse(self.xform1)
        self.xform2 = os.path.join(self.cwd, 'R1309_BEHAVE.xml')
        self.document2 = etree.parse(self.xform2)
        self.languages = os.path.join(self.cwd, 'site_languages.xlsx')
        self.languages_spaces = os.path.join(
            self.cwd, 'site_languages spaces.xlsx')
        self.languages_two_only = os.path.join(
            self.cwd, 'site_languages_two_only.xlsx')
        self.collect_settings = os.path.join(self.cwd, "collect.settings")
        self.test_output_path = os.path.join(self.cwd, 'editions')

    def tearDown(self):
        if os.path.isdir(self.test_output_path):
            for path in os.listdir(self.test_output_path):
                full_path = os.path.join(self.test_output_path, path)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path, ignore_errors=True)


class TestEditionsXML(TestEditionsBase):
    """XML manipulation related tests."""

    def test_map_xf_to_none_namespace(self):
        ns = Editions._map_xf_to_xform_namespace(self.document1)
        self.assertEqual(ns['xf'], 'http://www.w3.org/2002/xforms')

    def test_remove_xform_languages(self):
        """Should remove all but specified languages from the document,
        and mark the first language as the default."""
        doc = self.document1
        ns = Editions._map_xf_to_xform_namespace(doc)
        langs = ('german', 'french')
        updated = Editions._update_xform_languages(doc, ns, langs)
        langs_remaining = updated.getroot().xpath(
            './/xf:translation', namespaces=ns)
        self.assertEqual(len(langs_remaining), 2)
        default_lang = updated.getroot().xpath(
            './/xf:translation[@default="true()"]', namespaces=ns)
        self.assertEqual(default_lang[0].attrib['lang'], langs[0])

    def test_add_site_to_default_sid_no_sid(self):
        """Should not find a SID in this document, but log it for user info."""
        doc = self.document1
        ns = Editions._map_xf_to_xform_namespace(doc)
        site_code = '61200'

        with self.assertLogs(
                'odk_tools.language_editions.editions', level='INFO') as logs:
            Editions._add_site_to_default_sid(doc, ns, site_code)

        expected_log = ''.join([
            'INFO:odk_tools.language_editions.editions:Add to sid. ',
            'Site code: 61200, SIDs found: 0, Appended: False'])
        self.assertEqual(logs.output[0], expected_log)

        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid = doc.getroot().xpath(sid_xpath, namespaces=ns)
        self.assertEqual(len(sid), 0)

    def test_add_site_to_default_sid(self):
        """Should add the site code to the SID value."""
        doc = self.document2
        ns = Editions._map_xf_to_xform_namespace(doc)
        site_code = '61200'

        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid_start = doc.getroot().xpath(sid_xpath, namespaces=ns)[0].text
        updated = Editions._add_site_to_default_sid(doc, ns, site_code)
        sid_end = updated.getroot().xpath(sid_xpath, namespaces=ns)[0].text

        self.assertNotEqual(sid_start, sid_end)
        self.assertIn(site_code, sid_end)


class TestEditionsConfig(TestEditionsBase):
    """Configuration and setup related tests."""

    def test_read_site_language_list(self):
        """Should result in mapping of site codes to language lists."""
        langs = self.languages
        parsed = Editions._read_site_languages(langs)
        self.assertEqual(parsed['61221'], ('english',))
        self.assertEqual(parsed['11101'], ('english', 'spanish'))

    def test_read_site_language_list_spaces(self):
        """Should trim whitespace from the language list, if any."""
        langs = self.languages
        lang_spaces = self.languages_spaces
        langs_parsed = Editions._read_site_languages(langs)
        langs_spaces_parsed = Editions._read_site_languages(lang_spaces)
        self.assertEqual(langs_parsed, langs_spaces_parsed)

    def test_create_parser_without_args(self):
        """Should exit when no args provided."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                _create_parser().parse_args([])

    def test_create_parser_with_required_args(self):
        """Should parse the provided arguments and set defaults where needed."""
        xform = 'Q1302_BEHAVE.xml'
        sitelangs = 'site_languages.xlsx'
        args_list = [xform, sitelangs]
        args = _create_parser().parse_args(args_list)
        self.assertEqual(xform, args.xform)
        self.assertEqual(sitelangs, args.sitelangs)
        self.assertEqual(0, args.nested)

    def test_create_parser_with_all_args(self):
        """Should parse the provided arguments and pass in values."""
        xform = 'Q1302_BEHAVE.xml'
        sitelangs = 'site_languages.xlsx'
        nested = '--nested'
        args_list = [nested, xform, sitelangs]
        args = _create_parser().parse_args(args_list)
        self.assertEqual(xform, args.xform)
        self.assertEqual(sitelangs, args.sitelangs)
        self.assertEqual(1, args.nested)

    def test_write_editions_validation_xform(self):
        """Should raise a ValueError if the XForm path ext is not XML."""
        xform_invalid = "Q1302_BEHAVE.abc"
        with self.assertRaises(ValueError) as ar_context:
            Editions.write_language_editions(
                xform_path=xform_invalid, site_languages=self.languages,
                collect_settings=self.collect_settings)
        self.assertIn("XML", repr(ar_context.exception))

    def test_write_editions_validation_site_langs(self):
        """Should raise a ValueError if the site_lang path ext is not XLSX."""
        site_lang_invalid = "site_languages.abc"
        with self.assertRaises(ValueError) as ar_context:
            Editions.write_language_editions(
                xform_path=self.xform1, site_languages=site_lang_invalid,
                collect_settings=self.collect_settings)
        self.assertIn("XLSX", repr(ar_context.exception))

    def test_write_editions_validation_collect_settings(self):
        """Should raise a ValueError if the collect.settings base is wrong."""
        collect_settings_invalid = os.path.join(self.cwd, "collecting.set")
        with self.assertRaises(ValueError) as ar_context:
            Editions.write_language_editions(
                xform_path=self.xform1, site_languages=self.languages,
                collect_settings=collect_settings_invalid)
        self.assertIn("collect.settings", repr(ar_context.exception))


class TestEditionsJobs(TestEditionsBase):
    """Job preparation and execution related tests."""

    def test_prepare_zip_jobs_expected_content(self):
        """Should return expected number of jobs, with abs/rel path tuple."""
        languages = ('english', 'french')
        media_path = "Q1309_BEHAVE-media"
        source_path = os.path.join(self.cwd, media_path)
        observed = Editions._prepare_zip_jobs(
            source_path=source_path, languages=languages)
        self.assertEqual(198, len(observed))
        example_file = os.path.join(media_path, 'cesm_english.png')
        expected = (os.path.join(self.cwd, example_file), example_file)
        self.assertIn(expected, observed)

    def test_prepare_site_job_contains_expected_content(self):
        """Should include XForm XML file and a bunch of image copy specs."""
        jobs, xform_tuple = Editions._prepare_site_job(
            xform_path=self.xform1, site_code="61221", languages=("english",),
            nest_in_odk_folders=0, collect_settings=None)
        xform_name, xform = xform_tuple
        self.assertEqual(xform_name, os.path.basename(self.xform1))
        suffix = set(os.path.splitext(x[1])[1] for x in jobs)
        self.assertEqual({".png"}, suffix)

    def test_prepare_site_job_nest_contains_prefix(self):
        """Should return abs/rel tuple with odk/forms/ prefix to rel path"""
        jobs, _ = Editions._prepare_site_job(
            xform_path=self.xform1, site_code="61221", languages=("english",),
            nest_in_odk_folders=1, collect_settings=None)
        _, observed = jobs[0]
        prefix = os.path.join('odk', 'forms')
        self.assertTrue(observed.startswith(prefix))

    def test_prepare_site_job_collect_included(self):
        """Should include collect path in the zip job list."""
        collect_settings = "collect.settings"
        jobs, _ = Editions._prepare_site_job(
            xform_path=self.xform1, site_code="61221", languages=("english",),
            nest_in_odk_folders=1, collect_settings=collect_settings)
        observed = jobs[-1]
        expected = (collect_settings, os.path.join('odk', collect_settings))
        self.assertEqual(expected, observed)

    def test_prepare_site_job_collect_included_no_nest(self):
        """Should include collect path in the zip job list, even for no nest."""
        collect_settings = "collect.settings"
        jobs, _ = Editions._prepare_site_job(
            xform_path=self.xform1, site_code="61221", languages=("english",),
            nest_in_odk_folders=0, collect_settings=collect_settings)
        observed = jobs[-1]
        expected = (collect_settings, os.path.join('odk', collect_settings))
        self.assertEqual(expected, observed)

    def test_write_multiple_forms_for_same_sites_merges(self):
        """Should merge multiple runs into same site zip files."""
        Editions.write_language_editions(
            xform_path=self.xform1, site_languages=self.languages_two_only,
            nest_in_odk_folders=1, collect_settings=self.collect_settings)
        Editions.write_language_editions(
            xform_path=self.xform2, site_languages=self.languages_two_only,
            nest_in_odk_folders=1, collect_settings=self.collect_settings)
        output_files = os.listdir(self.test_output_path)
        first_zip = os.path.join(self.test_output_path, output_files[0])
        with zipfile.ZipFile(first_zip) as zip_out:
            zip_items = zip_out.namelist()
        self.assertEqual(387, len(zip_items))
        self.assertEqual(2, len(output_files))

    def test_write_no_duplicate_file_warnings(self):
        """Should not have any duplicate file warnings when creating zips."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Editions.write_language_editions(
                xform_path=self.xform1, site_languages=self.languages_two_only,
                nest_in_odk_folders=1, collect_settings=self.collect_settings)
            Editions.write_language_editions(
                xform_path=self.xform1, site_languages=self.languages_two_only,
                nest_in_odk_folders=1, collect_settings=self.collect_settings)
        self.assertEqual(0, len(w))
