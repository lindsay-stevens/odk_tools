import unittest
import os
import shutil
from lxml import etree
from odk_tools.language_editions.editions import Editions


class TestEditions(unittest.TestCase):

    def setUp(self):
        xform1 = 'Q1309_BEHAVE.xml'
        self.document1 = etree.parse(xform1)
        xform2 = 'R1309_BEHAVE.xml'
        self.document2 = etree.parse(xform2)
        self.languages = 'site_languages.xlsx'

    def test_map_xf_to_none_namespace(self):
        ns = Editions.map_xf_to_xform_namespace(self.document1)
        self.assertEqual(ns['xf'], 'http://www.w3.org/2002/xforms')

    def test_remove_xform_languages(self):
        """Should remove all but specified languages from the document,
        and mark the first language as the default."""
        doc = self.document1
        ns = Editions.map_xf_to_xform_namespace(doc)
        langs = ['german', 'french']
        updated = Editions.update_xform_languages(doc, ns, langs)
        langs_remaining = updated.getroot().xpath(
            './/xf:translation', namespaces=ns)
        self.assertEqual(len(langs_remaining), 2)
        default_lang = updated.getroot().xpath(
            './/xf:translation[@default="true()"]', namespaces=ns)
        self.assertEqual(default_lang[0].attrib['lang'], langs[0])

    def test_add_site_to_default_sid_no_sid(self):
        """Should not find a SID in this document, but log it for user info."""
        doc = self.document1
        ns = Editions.map_xf_to_xform_namespace(doc)
        site_code = '61200'

        with self.assertLogs(
                'odk_tools.language_editions', level='INFO') as logs:
            Editions.add_site_to_default_sid(doc, ns, site_code)

        expected_log = ''.join([
            'INFO:odk_tools.language_editions:Add to sid. ',
            'Site code: 61200, SIDs found: 0, Appended: False'])
        self.assertEqual(logs.output[0], expected_log)

        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid = doc.getroot().xpath(sid_xpath, namespaces=ns)
        self.assertEqual(len(sid), 0)

    def test_add_site_to_default_sid(self):
        """Should add the site code to the SID value."""
        doc = self.document2
        ns = Editions.map_xf_to_xform_namespace(doc)
        site_code = '61200'

        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid_start = doc.getroot().xpath(sid_xpath, namespaces=ns)[0].text
        updated = Editions.add_site_to_default_sid(doc, ns, site_code)
        sid_end = updated.getroot().xpath(sid_xpath, namespaces=ns)[0].text

        self.assertNotEqual(sid_start, sid_end)
        self.assertIn(site_code, sid_end)

    def test_read_site_language_list(self):
        """Should result in mapping of site codes to language lists."""
        langs = self.languages
        parsed = Editions.read_site_languages(langs)
        self.assertEqual(parsed['61212'], ['english'])
        self.assertEqual(parsed['11101'], ['english', 'spanish'])

    def test_create_output_directory(self):
        """Should create a directory tree."""
        parent_folder = 'editions'
        site_code = '12345'
        media_folder = 'Q1309_BEHAVE-media'

        expected_folder = os.path.join(parent_folder, site_code, media_folder)
        self.assertFalse(os.path.isdir(expected_folder))

        Editions.create_output_directory(parent_folder, site_code, media_folder)
        self.assertTrue(os.path.isdir(expected_folder))

        shutil.rmtree(parent_folder)


