import unittest
import os
import shutil
import glob
import itertools
import zipfile
from lxml import etree
from odk_tools.language_editions.editions import Editions


class TestEditions(unittest.TestCase):

    def setUp(self):
        self.xform1 = 'Q1309_BEHAVE.xml'
        self.document1 = etree.parse(self.xform1)
        self.xform2 = 'R1309_BEHAVE.xml'
        self.document2 = etree.parse(self.xform2)
        self.languages = 'site_languages.xlsx'
        self.z7zip_path = 'C:/Program Files/7-Zip/7z.exe'

    def test_map_xf_to_none_namespace(self):
        ns = Editions._map_xf_to_xform_namespace(self.document1)
        self.assertEqual(ns['xf'], 'http://www.w3.org/2002/xforms')

    def test_remove_xform_languages(self):
        """Should remove all but specified languages from the document,
        and mark the first language as the default."""
        doc = self.document1
        ns = Editions._map_xf_to_xform_namespace(doc)
        langs = ['german', 'french']
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
                'odk_tools.language_editions', level='INFO') as logs:
            Editions._add_site_to_default_sid(doc, ns, site_code)

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
        ns = Editions._map_xf_to_xform_namespace(doc)
        site_code = '61200'

        sid_xpath = './/xf:instance//xf:visit/xf:sid'
        sid_start = doc.getroot().xpath(sid_xpath, namespaces=ns)[0].text
        updated = Editions._add_site_to_default_sid(doc, ns, site_code)
        sid_end = updated.getroot().xpath(sid_xpath, namespaces=ns)[0].text

        self.assertNotEqual(sid_start, sid_end)
        self.assertIn(site_code, sid_end)

    def test_read_site_language_list(self):
        """Should result in mapping of site codes to language lists."""
        langs = self.languages
        parsed = Editions._read_site_languages(langs)
        self.assertEqual(parsed['61212'], ['english'])
        self.assertEqual(parsed['11101'], ['english', 'spanish'])

    def test_create_output_directory(self):
        """Should create a directory tree."""
        parent_path = 'editions_create'
        site_code = '12345'
        media_folder = 'Q1309_BEHAVE-media'

        expected_folder = os.path.join(parent_path, site_code, media_folder)
        self.assertFalse(os.path.isdir(expected_folder))

        Editions._create_output_directory(parent_path, site_code, media_folder)
        self.assertTrue(os.path.isdir(expected_folder))

        shutil.rmtree(parent_path, ignore_errors=True)

    def test_copy_images_for_languages(self):
        """Should copy images for the specified languages."""
        parent_path = 'editions_copy'
        site_code = '99999'
        source_media_folder = 'R1309_BEHAVE-media'
        langs = ['english', 'french']

        site_dir, target_media_dir = Editions._create_output_directory(
            parent_path, site_code, source_media_folder)

        find_images = [glob.glob('{0}/*_{1}.png'.format(
            source_media_folder, x)) for x in langs]
        images_count = len(tuple(itertools.chain.from_iterable(find_images)))

        Editions._copy_images_for_languages(
            source_media_folder, target_media_dir, langs)
        copied_images = len(os.listdir(target_media_dir))

        self.assertEqual(images_count, copied_images)

        shutil.rmtree(parent_path, ignore_errors=True)

    def test_prepare_zip_job(self):
        """Should result in a zip command."""
        observed = Editions._prepare_zip_job('7zip', 'source', 'form', 'site')
        expected = '7zip a -tzip -mx9 -sdel form-site.zip "source/form*"'
        self.assertEqual(expected, observed)

    def test_zip_concurrently(self):
        """Should result in a zip file named by site, with expected images."""
        curdir = os.path.dirname(__file__)
        parent_path = os.path.join(curdir, 'editions_zip')
        site_code = '61202'
        form_name = 'Q1309_BEHAVE'
        source_media_folder = 'Q1309_BEHAVE-media'
        langs = ['english', 'norwegian', 'german']
        find_images = [glob.glob('{0}/*_{1}.png'.format(
            source_media_folder, x)) for x in langs]
        images_count = len(tuple(itertools.chain.from_iterable(find_images)))

        site_dir, target_media_dir = Editions._create_output_directory(
            parent_path, site_code, source_media_folder)
        Editions._copy_images_for_languages(
            source_media_folder, target_media_dir, langs)
        job = Editions._prepare_zip_job(
            self.z7zip_path, site_dir, form_name, site_code)
        Editions._zip_concurrently([job], [site_dir])

        observed_files = os.listdir(parent_path)[0]
        expected_files = '{0}-{1}.zip'.format(form_name, site_code)
        self.assertEqual(expected_files, observed_files)

        zip_path = os.path.join(parent_path, expected_files)
        zip_out = zipfile.ZipFile(zip_path)
        zip_item_count = len(zip_out.infolist())
        zip_out.close()
        self.assertEqual(images_count + 1, zip_item_count)

        shutil.rmtree(parent_path, ignore_errors=True)

    def test_language_editions(self):
        """Should process all listed sites into zip files."""
        xform_path = os.path.realpath(self.xform1)
        site_langs_path = os.path.realpath('site_languages.xlsx')
        z7zip_path = self.z7zip_path
        Editions.language_editions(xform_path, site_langs_path, z7zip_path)

        observed = len(glob.glob('editions/*.zip'))
        expected = len(Editions._read_site_languages(site_langs_path))
        self.assertEqual(expected, observed)

        shutil.rmtree('editions', ignore_errors=True)
