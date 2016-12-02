from odk_tools.gui import xform_patch
from odk_tools.gui.wrappers import generate_xform, validate_xform
from tests.gui import FixturePaths
import unittest
import os
import xmltodict


class TestXFormPatch(unittest.TestCase):

    def setUp(self):
        self.fixtures = FixturePaths()
        self.xml_template = """<?xml version="1.0" encoding="utf-8"?>
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
        self.clean_up_file = None

    def tearDown(self):
        if self.clean_up_file is not None:
            os.remove(self.clean_up_file)

    def test_xform_empty_question_label_patch_content_add(self):
        """Should add a blank value in the text node where one doesn"t exist."""
        xml_template = self.xml_template
        expected = "&nbsp;"
        xml_input = xml_template.format("")
        parsed, _ = xform_patch._xform_empty_question_label_patch_content(
            xml_input)
        itext = parsed["h:html"]["h:head"]["model"]["itext"]
        observed = itext["translation"][0]["text"][0]["value"]
        self.assertIn(expected, observed)

    def test_xform_empty_question_label_patch_content_no_overwrite(self):
        """Should not overwrite plain text itext values that already exist."""
        xml_template = self.xml_template
        expected = "My plain string itext question label"
        xml_input = xml_template.format(
            """<value>{0}</value>""".format(expected))
        observed, _ = xform_patch._xform_empty_question_label_patch_content(
            xml_input)
        parsed, _ = xform_patch._xform_empty_question_label_patch_content(
            xml_input)
        itext = parsed["h:html"]["h:head"]["model"]["itext"]
        observed = itext["translation"][0]["text"][0]["value"][1]["#text"]
        self.assertEqual(expected, observed)

    def test_xform_empty_question_label_patch_with_full_xlsform(self):
        """Should insert patch values to all text value elements."""
        xlsform_path = self.fixtures.files["Q1302_BEHAVE.xlsx"]
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.clean_up_file = xform_path
        generate_xform.wrapper(xlsform_path=xlsform_path)
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
        xlsform_path = self.fixtures.files["Q1302_BEHAVE.xlsx"]
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.clean_up_file = xform_path
        generate_xform.wrapper(xlsform_path=xlsform_path)
        observed = validate_xform.wrapper(
            java_path='', validate_path=validate_xform._locate_odk_validate(),
            xform_path=xform_path)
        if isinstance(observed, list):
            observed = "".join(observed)
        expected = "Xform is valid"
        self.assertIn(expected, observed)

    def test_xform_empty_question_label_patch_validates_ok_unicode(self):
        """Should pass validate step without errors."""
        xlsform_path = self.fixtures.files["R1405_BEHAVE.xlsx"]
        # 1405 includes a whole lot of unicode characters.
        xform_path = xlsform_path.replace("xlsx", "xml")
        self.clean_up_file = xform_path
        generate_xform.wrapper(xlsform_path=xlsform_path)
        observed = validate_xform.wrapper(
            java_path='', validate_path=validate_xform._locate_odk_validate(),
            xform_path=xform_path)
        if isinstance(observed, list):
            observed = "".join(observed)
        expected = "Xform is valid"
        self.assertIn(expected, observed)


