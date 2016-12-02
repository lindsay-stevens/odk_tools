import logging
from odk_tools.gui import utils
from odk_tools.language_editions.editions import Editions
from odk_tools.gui.log_capturing_handler import CapturingHandler


def wrapper(xform_path, sitelangs_path, nest_in_odk_folders,
            collect_settings=None):
    """
    Return edition generation result, including any stderr / stdout content.

    If the paths is not resolved, error message boxes are opened to
    indicate this clearly to the user.

    Parameters.
    :param xform_path: str. Path to XLSForm to convert.
    :param sitelangs_path: str. Path to site languages spreadsheet.
    :param nest_in_odk_folders: int. 1=yes, 0=no. Nest in /odk/forms/*.
    :param collect_settings: Path to collect.settings file to include
        in nested output folders.
    :return: tuple (output header message, message content)
    """
    try:
        header = "Generate Editions task was run. Output below."
        valid_xform_path = utils.validate_path("XForm path", xform_path, ".xml")
        valid_sitelang_path = utils.validate_path(
            "Site Languages path", sitelangs_path, ".xlsx")
        if collect_settings is None:
            collect_settings = ""

        if len(collect_settings) == 0:
                valid_settings, valid_settings_path = True, None
        else:
            valid_settings_path = utils.validate_path(
                "Collect settings path", collect_settings, ".settings")
        editions_log = logging.getLogger('odk_tools.language_editions.editions')
        editions_log.setLevel('DEBUG')
        log_capture = CapturingHandler(logger=editions_log)
        content = log_capture.watcher.output
        Editions.write_language_editions(
            xform_path=valid_xform_path,
            site_languages=valid_sitelang_path,
            nest_in_odk_folders=nest_in_odk_folders,
            collect_settings=valid_settings_path)
    except Exception as e:
        header = "Generate Editions task not run. Error(s) below."
        content = str(e)
    result = utils.format_output(header=header, content=content)
    return result
