import unittest
import os
import shutil
import glob
import itertools
import zipfile
from lxml import etree
from odk_tools.language_editions.editions import Editions, _create_parser


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
        self.languages_two_only = os.path.join(self.cwd,
                                               'site_languages_two_only.xlsx')
        self.z7zip_path = 'C:/Program Files/7-Zip/7z.exe'
        self.test_output_path = ''

    def tearDown(self):
        if self.test_output_path.endswith('editions'):
            for path in os.listdir(self.test_output_path):
                full_path = os.path.join(self.test_output_path, path)
                if os.path.isfile(full_path):
                    os.remove(full_path)
                if os.path.isdir(full_path):
                    os.rmdir(full_path)
        else:
            shutil.rmtree(self.test_output_path, ignore_errors=True)


class TestEditions(TestEditionsBase):

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

    def test_read_site_language_list(self):
        """Should result in mapping of site codes to language lists."""
        langs = self.languages
        parsed = Editions._read_site_languages(langs)
        self.assertEqual(parsed['61221'], ['english'])
        self.assertEqual(parsed['11101'], ['english', 'spanish'])

    def test_read_site_language_list_spaces(self):
        """Should trim whitespace from the language list, if any."""
        langs = self.languages
        lang_spaces = self.languages_spaces
        langs_parsed = Editions._read_site_languages(langs)
        langs_spaces_parsed = Editions._read_site_languages(lang_spaces)
        self.assertEqual(langs_parsed, langs_spaces_parsed)

    def test_create_output_directory(self):
        """Should create a directory tree."""
        parent_path = os.path.join(self.cwd, 'editions_create')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '12345'
        media_folder = 'Q1309_BEHAVE-media'

        expected_folder = os.path.join(parent_path, site_code, media_folder)
        self.assertFalse(os.path.isdir(expected_folder))

        Editions._create_output_directory(parent_path, site_code, media_folder)
        self.assertTrue(os.path.isdir(expected_folder))

    def test_copy_images_for_languages(self):
        """Should copy images for the specified languages."""
        parent_path = os.path.join(self.cwd, 'editions_copy')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '99999'
        source_media_folder_name = 'R1309_BEHAVE-media'
        source_media_folder = os.path.join(self.cwd, source_media_folder_name)
        langs = ['english', 'french']

        site_dir, target_media_dir = Editions._create_output_directory(
            parent_path, site_code, source_media_folder_name)

        find_images = [glob.glob('{0}/*_{1}.png'.format(
            source_media_folder, x)) for x in langs]
        images_count = len(tuple(itertools.chain.from_iterable(find_images)))

        Editions._copy_images_for_languages(
            source_media_folder, target_media_dir, langs)
        copied_images = len(os.listdir(target_media_dir))

        self.assertEqual(images_count, copied_images)

    def test_prepare_zip_job(self):
        """Should result in a zip command."""
        observed = Editions._prepare_zip_job('7zip', 'source', 'form', 'site')
        expected = '7zip a -tzip -mx9 -sdel "site.zip" "/*"'
        self.assertEqual(expected, observed)

    def test_execute_zip_jobs_produces_site_zip(self):
        """Should result in a zip file named by site."""
        parent_path = os.path.join(self.cwd, 'editions_zip')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '61202'
        form_name = 'Q1309_BEHAVE'
        langs = ['english', 'norwegian', 'german']

        site_path = Editions._prepare_site_files(
            parent_path, self.xform1, site_code, langs)
        job = Editions._prepare_zip_job(
            self.z7zip_path, site_path, form_name, site_code)
        Editions._execute_zip_jobs([job])

        observed_files = [x for x in os.listdir(parent_path) if x.endswith('.zip')]
        expected_files = '{0}.zip'.format(site_code)
        self.assertEqual([expected_files], observed_files)

    def test_execute_zip_jobs_output_path_with_spaces(self):
        """Should result in a zip file, even if output path has a space."""
        parent_path = os.path.join(self.cwd, 'editions space')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '61202'
        form_name = 'Q1309_BEHAVE'
        langs = ['english']

        site_path = Editions._prepare_site_files(
            parent_path, self.xform1, site_code, langs)
        job = Editions._prepare_zip_job(
            self.z7zip_path, site_path, form_name, site_code)
        Editions._execute_zip_jobs([job])

        observed_files = [x for x in os.listdir(parent_path) if x.endswith('.zip')]
        expected_files = '{0}.zip'.format(site_code)
        self.assertEqual([expected_files], observed_files)

    def test_execute_zip_jobs_zip_contents_correct(self):
        """Should result in a zip file contains expected images & paths."""
        parent_path = os.path.join(self.cwd, 'editions_zip')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '61202'
        form_name = 'Q1309_BEHAVE'
        expected_zip = os.path.join(parent_path, '{0}.zip'.format(site_code))
        source_media_folder_name = 'Q1309_BEHAVE-media'
        source_media_folder = os.path.join(self.cwd, source_media_folder_name)
        langs = ['english']
        find_images = [glob.glob('{0}/*_{1}.png'.format(
            source_media_folder, x)) for x in langs]
        images_found = list(itertools.chain.from_iterable(find_images))

        site_path = Editions._prepare_site_files(
            parent_path, self.xform1, site_code, langs)
        job = Editions._prepare_zip_job(
            self.z7zip_path, site_path, form_name, site_code)
        Editions._execute_zip_jobs([job])

        zip_path = os.path.join(parent_path, expected_zip)
        zip_out = zipfile.ZipFile(zip_path)
        zip_items = zip_out.infolist()
        zip_out.close()

        non_image_contents = [source_media_folder, '{0}.xml'.format(form_name)]
        expected_contents = non_image_contents + images_found
        self.assertEqual(
            sorted([os.path.normpath(
                os.path.join(self.cwd, x)) for x in expected_contents]),
            sorted([os.path.normpath(
                os.path.join(self.cwd, x.filename)) for x in zip_items])
        )

    def test_clean_up_site_dirs(self):
        """Should remove all empty site dirs."""
        parent_path = os.path.join(self.cwd, 'editions_zip')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '61310'
        form_name = 'Q1309_BEHAVE'
        langs = ['english']

        site_path = Editions._prepare_site_files(
            parent_path, self.xform1, site_code, langs)
        job = Editions._prepare_zip_job(
            self.z7zip_path, site_path, form_name, site_code)

        Editions._execute_zip_jobs([job])
        pre_cleanup = [
            x for x in os.listdir(parent_path) if not x.endswith('.zip')]
        self.assertEqual(1, len(pre_cleanup))
        Editions._clean_up_empty_site_dirs([site_path])
        post_cleanup = [
            x for x in os.listdir(parent_path) if not x.endswith('.zip')]
        self.assertEqual(0, len(post_cleanup))

    def test_create_parser_without_args(self):
        """Should exit when no args provided."""
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
        self.assertEqual('C:\\Program Files\\7-Zip\\7z.exe', args.zipexe)
        self.assertEqual(False, args.concurrently)
        self.assertEqual(0, args.nested)

    def test_create_parser_with_all_args(self):
        """Should parse the provided arguments and pass in values."""
        xform = 'Q1302_BEHAVE.xml'
        sitelangs = 'site_languages.xlsx'
        zipexe = 'C:\\Program Files\\7-Zippy\\7z.exe'
        zipexe_arg = '--zipexe=' + zipexe
        concurrently = '--concurrently'
        nested = '--nested'
        args_list = [zipexe_arg, concurrently, nested, xform, sitelangs]
        args = _create_parser().parse_args(args_list)
        self.assertEqual(xform, args.xform)
        self.assertEqual(sitelangs, args.sitelangs)
        self.assertEqual(zipexe, args.zipexe)
        self.assertEqual(True, args.concurrently)
        self.assertEqual(1, args.nested)

    def test_execute_zip_jobs_merge_2_forms_zip_contents_correct(self):
        """Should result in a zip file contains expected images & paths."""
        parent_path = os.path.join(self.cwd, 'editions')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        site_code = '61202'
        zip_output = os.path.join(parent_path, '{0}.zip'.format(site_code))
        form_names = (('Q1309_BEHAVE', self.xform1),
                      ('R1309_BEHAVE', self.xform2))
        expected = []
        for form_name, xform in form_names:
            src_media_folder_name = '{0}-media'.format(form_name)
            src_media_folder = os.path.join(self.cwd, src_media_folder_name)
            expected += [src_media_folder, '{0}.xml'.format(form_name)]

            langs = ['english']
            find_images = [glob.glob('{0}/*_{1}.png'.format(
                src_media_folder, x)) for x in langs]
            expected += list(itertools.chain.from_iterable(find_images))

            site_path = Editions._prepare_site_files(
                parent_path, xform, site_code, langs)
            job = Editions._prepare_zip_job(
                self.z7zip_path, site_path, form_name, site_code)
            Editions._execute_zip_jobs([job])
            Editions._clean_up_empty_site_dirs(site_dirs=[site_path])

        with zipfile.ZipFile(os.path.join(parent_path, zip_output)) as zip_out:
            zip_items = zip_out.infolist()
        expected_sort = sorted([os.path.normpath(
            os.path.join(self.cwd, x)) for x in expected])
        observed_sort = sorted([os.path.normpath(
            os.path.join(self.cwd, x.filename)) for x in zip_items])
        self.assertEqual(expected_sort, observed_sort)


class TestEditionsSlow(TestEditionsBase):
    """Tests that are slow, generally end-to-end type tests."""

    def test_language_editions(self):
        """Should process all listed sites into zip files."""
        parent_path = os.path.join(self.cwd, 'editions')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)

        xform_path = self.xform1
        site_langs_path = self.languages
        z7zip_path = self.z7zip_path
        Editions.language_editions(xform_path, site_langs_path, z7zip_path,
                                   nest_in_odk_folders=0)

        observed = len(glob.glob('{0}/editions/*.zip'.format(self.cwd)))
        expected = len(Editions._read_site_languages(site_langs_path))
        self.assertEqual(expected, observed)

    def test_language_editions_nest_in_odk_folders(self):
        """Should place output under /odk/forms/* """
        parent_path = os.path.join(self.cwd, 'editions')
        self.test_output_path = parent_path
        shutil.rmtree(parent_path, ignore_errors=True)
        form_names = (('Q1309_BEHAVE', self.xform1),
                      ('R1309_BEHAVE', self.xform2))
        for form_name, xform in form_names:
            Editions.language_editions(
                xform_path=xform, site_languages=self.languages_two_only,
                z7zip_path=self.z7zip_path, nest_in_odk_folders=1)

        site_settings = (('12501', ('french', 'english')),
                         ('41101', ('german',)))
        for site_code, langs in site_settings:

            expected = []
            for form_name, xform in form_names:
                src_media_folder_name = '{0}-media'.format(form_name)
                src_media_folder = os.path.join(self.cwd, src_media_folder_name)
                expected += [src_media_folder_name, '{0}.xml'.format(form_name)]
                find_images = [glob.glob('{0}/*_{1}.png'.format(
                    src_media_folder, x)) for x in langs]
                expect_images = list(itertools.chain.from_iterable(find_images))
                expect_images = [os.path.join(os.path.split(os.path.dirname(x))[1], os.path.split(x)[1]) for x in expect_images]
                expected += expect_images
            expected += [os.path.join(self.cwd, 'odk'), os.path.join(self.cwd, 'odk', 'forms'),]

            output = os.path.join(parent_path, '{0}.zip'.format(site_code))
            with zipfile.ZipFile(os.path.join(parent_path, output)) as zip_out:
                zip_items = zip_out.infolist()
            expected_sort = sorted([os.path.normpath(
                os.path.join(self.cwd, 'odk', 'forms', x)) for x in expected])
            observed_sort = sorted([os.path.normpath(
                os.path.join(self.cwd, x.filename)) for x in zip_items])
            self.assertEqual(expected_sort, observed_sort)