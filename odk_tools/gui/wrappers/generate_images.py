from odk_tools.gui import utils
from odk_tools.gui.log_capturing_handler import CapturingHandler
import logging
from odk_tools.question_images import images


def wrapper(xlsform_path):
    """
    Return image generation result, including any stderr / stdout content.

    Calls write_images using the supplied xlsform_path.
    - XLSForm path is always required.

    If the paths is not resolved, error message boxes are opened to
    indicate this clearly to the user.

    Parameters.
    :param xlsform_path: str. Path to XLSForm to convert.
    :return: tuple (output header message, message content)
    """
    try:
        valid_xlsform_path = utils.validate_path(
            "XLSForm path", xlsform_path, ".xlsx")
        header = "Generate Images task was run. Output below."
        images_log = logging.getLogger('odk_tools.question_images.images')
        images_log.setLevel("DEBUG")
        log_capture = CapturingHandler(logger=images_log)
        content = log_capture.watcher.output
        images.write_images(xlsform_path=valid_xlsform_path)
    except Exception as e:
        header = "Generate Images task not run. Error(s) below."
        content = str(e)
    result = utils.format_output(header=header, content=content)
    return result
