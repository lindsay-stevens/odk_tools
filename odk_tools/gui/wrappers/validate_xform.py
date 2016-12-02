import os
import subprocess
import sys
from odk_tools.gui import utils


def get_popen_kwargs():
    """Because accidentally changing global dictionaries is all too easy."""
    return {
        'universal_newlines': True, 'cwd': os.path.expanduser("~"),
        'stdin': subprocess.PIPE, 'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE}


def _get_callable_java_path(popen_kwargs):
    """
    Check if Java can be invoked from JAVA_HOME, and return the exec path.

    Parameters.
    :param popen_kwargs: dict. Options to pass through to subprocess.Popen.
    :return: bool (working java -version), str (path to java)
    """
    found = False
    path = ''
    java_home = os.environ.get('JAVA_HOME')
    if java_home is not None:
        if os.name == "nt":
            path = '"{}"'.format(os.path.join(java_home, "bin", "java.exe"))
        else:
            path = os.path.join(java_home, "bin", "java")
        cmd = '{} -version'.format(path)
        with subprocess.Popen(cmd, **popen_kwargs) as p:
            output = p.stderr.read()
        found = output.startswith('java version')
    if not found:
        msg = "Java does not appear to be callable. Please either:\n" \
              "- Enter a path to the location of 'java.exe', or\n" \
              "- Select the path using the 'Browse...' button, or\n" \
              "- Set the 'JAVA_HOME' environment variable and restart the GUI."
        raise ValueError(msg)
    return utils.validate_path("Java Path", path, ".exe")


def _locate_odk_validate():
    """
    Check if ODK_Validate is in the current directory.

    As a script, __file__ works, but as a frozen / pyinstaller exe, the
    sys.executable is required to get the right path.

    Adapted from http://stackoverflow.com/a/404750.

    :return: str. Absolute path to "ODK_Validate.jar".
    """
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(__file__)
        while "setup.py" not in os.listdir(path):
            path = os.path.dirname(path)
        application_path = os.path.join(path, "bin")
    return os.path.join(application_path, 'ODK_Validate.jar')


def _call_odk_validate(cmd, env, popen_kwargs):
    """Mock-able call to Popen."""
    with subprocess.Popen(cmd, env=env, **popen_kwargs) as p:
            content = [p.stderr.read(), p.stdout.read()]
    return content


def wrapper(java_path, validate_path, xform_path):
    """
    Return ODK_Validate result, guessing at java and odk_validate location.

    Calls ODK_Validate.jar using Java and the supplied XForm XML path.
    - If java_path is blank, try to find it from JAVA_HOME environment var.
    - If validate_path is blank, try to find it in the current directory.
    - XForm path is always required.

    If any of the paths end up not being resolved, error message boxes are
    opened to indicate this clearly to the user.

    Parameters.
    :param java_path: str. Path to java binary.
    :param validate_path: str. Path to ODK_Validate.jar.
    :param xform_path: str. Path to XForm XML file to validate.
    :return: tuple (output header message, message content)
    """
    try:
        header = "Validate XForm task was run. Output below."
        if len(java_path) == 0:
            valid_java_path = _get_callable_java_path(
                popen_kwargs=get_popen_kwargs())
        else:
            valid_java_path = utils.validate_path(
                "Java path", java_path, ".exe")
        if len(validate_path) == 0:
            validate_path = _locate_odk_validate()
        valid_validate_path = utils.validate_path(
            "ODK_Validate path", validate_path, ".jar")
        valid_xform_path = utils.validate_path("XForm path", xform_path, ".xml")

        cmd = ['java', '-jar', valid_validate_path, valid_xform_path]
        env = {'PATH': valid_java_path}
        content = _call_odk_validate(
            cmd=cmd, env=env, popen_kwargs=get_popen_kwargs())
    except Exception as e:
        header = "Validate XForm task not run. Error(s) below."
        content = str(e)
    result = utils.format_output(header=header, content=content)
    return result
