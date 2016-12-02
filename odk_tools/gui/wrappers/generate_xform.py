from pyxform.xls2xform import xls2xform_convert
from odk_tools.gui import utils, xform_patch


def wrapper(xlsform_path):
    """
    Return XLS2XForm result, including any generated warnings.

    Calls xls2xform_convert using the supplied xlsform_path.
    - XLSForm path is always required.
    - If xform_path is blank, use the XLSForm filename and path.

    If any of the paths end up not being resolved, error message boxes are
    opened to indicate this clearly to the user.

    Parameters.
    :param xlsform_path: str. Path to XLSForm to convert.
    :return: tuple (output header message, message content)
    """
    xform_path_used = None
    xlsform_path_used = None
    try:
        header = "Generate XForm task was run. Output below."
        valid_xlsform_path = utils.validate_path(
            "XLSForm path", xlsform_path, ".xlsx")
        valid_xform_path = valid_xlsform_path.replace(".xlsx", ".xml")
        content = xls2xform_convert(
            xlsform_path=valid_xlsform_path, xform_path=valid_xform_path,
            validate=False)
        content.append(xform_patch.xform_empty_question_label_patch(
            valid_xform_path))
    except Exception as e:
        header = "Generate XForm task not run. Error(s) below."
        content = str(e)
    else:
        xform_path_used = valid_xform_path
        xlsform_path_used = valid_xlsform_path
    result = utils.format_output(header=header, content=content)
    return result, xform_path_used, xlsform_path_used
