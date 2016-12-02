import xmltodict


def xform_empty_question_label_patch(xform_path):
    """
    Insert blank question labels if none exist, to avoid bug in ODK Collect.

    Issue present in ODK Collect v.1.4.10 r1061 where if a question does
    not have a plain text label defined, the question overview activity
    will cause an app crash. Specifically, when editing / resuming a saved
    xform instance, the TextUtils markdown converter throws an NPE.

    This function guards against that by inserting a blank question label
    text, which avoids the NPE but doesn't affect the form appearance. The
    text inserted is a HTML-encoded non-blank space: "&amp;nbsp;".

    :param xform_path: Path to XForm to patch.
    :type xform_path: str
    :return: Result of patch action.
    :rtype: str
    """
    try:
        with open(xform_path, mode='r', encoding="UTF-8") as xform_file:
            xform_content = xform_file.read()
        xform_fixed, status = _xform_empty_question_label_patch_content(
            xform_content)
        xform_fixed_xml = xmltodict.unparse(
                xform_fixed, ordered_mixed_children=True,
                short_empty_elements=True)
        with open(xform_path, mode='w', encoding="UTF-8") as fixed:
            fixed.write(xform_fixed_xml)
    except OSError as ose:
        status = "Error during itext value patch:\n{0}".format(str(ose))
    return status


def _xform_empty_question_label_patch_content(xform_content):
    """
    Find all image-only question itext and add a blank plain text label.

    Separate function because IO.

    The parse parameter force_list ensures that even single values
    of that element name will be in a list, so that we don't accidentally
    loop through the characters of a string.

    :param xform_content: XForm XML content to be modified.
    :type xform_content: str
    :return: (Patched XForm XML, status_message)
    :rtype: tuple(collections.OrderedDict, str)
    """
    status_message = ""
    force_list = ("bind", "translation", "text", "value")
    xml_dict = xmltodict.parse(xform_content, force_list=force_list,
                               ordered_mixed_children=True)
    xml_model = xml_dict["h:html"]["h:head"]["model"]
    for bound_item in xml_model["bind"]:
        for translation in xml_model["itext"]["translation"]:
            for itext_item in translation["text"]:
                itext_item_id = itext_item.get("@id")
                bound_item_nodeset = bound_item.get("@nodeset")
                if itext_item_id is None or bound_item_nodeset is None:
                    continue
                bound_item_ref = "{0}:label".format(bound_item_nodeset)
                itext_ref_match = itext_item_id == bound_item_ref
                itext_item_value = itext_item.get("value")
                has_plain_text_value = False
                for text_value in itext_item_value:
                    if "@form" not in text_value:
                        has_plain_text_value = True
                    elif text_value.get("@form") in ["short", "long"]:
                        has_plain_text_value = True
                if itext_ref_match and not has_plain_text_value:
                    itext_item_value.append("&nbsp;")
                    status_message = "Added itext value patch (&nbsp; fix)."
    return xml_dict, status_message
