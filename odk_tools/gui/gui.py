import tkinter
import tkinter.filedialog
import tkinter.messagebox
from tkinter import ttk
import os
import sys
import subprocess
from pyxform.xls2xform import xls2xform_convert
from pyxform.errors import PyXFormError
from odk_tools.question_images import images
from odk_tools.language_editions import editions
from odk_tools import __version__
import logging
import collections
import xmltodict


class _CapturingHandler(logging.Handler):
    """
    A logging handler capturing all (raw and formatted) logging output.

    Largely the same as doing "from unittest.case import _CapturingHandler",
    but copied here because it is a simple class, and the original has an
    underscore prefix so it might change unexpectedly.

    Usage:
    Here's how to attach it to a logger, get the logs, and then detach it.

    my_logger = logging.getLogger(name="logger_name")
    capture_handler = _CapturingHandler(logger=my_logger)
    log_messages = capture_handler.watcher.output
    log_records = capture_handler.watcher.records
    my_logger.removeHandler(hdlr=capture_handler)
    """

    def __init__(self, logger):
        logging.Handler.__init__(self)
        _LoggingWatcher = collections.namedtuple(
            "_LoggingWatcher", ["records", "output"])
        self.watcher = _LoggingWatcher([], [])
        logger.addHandler(self)

    def flush(self):
        pass

    def emit(self, record):
        self.watcher.records.append(record)
        msg = self.format(record)
        self.watcher.output.append(msg)


class ODKToolsGui:

    def __init__(self, master=None):
        """
        Set up the GUI by creating controls and adding them to the master frame.

        Controls appear in the GUI in the order they were added. Since many of
        the controls are similar, the repetitive parts of the process are
        abstracted to helper functions. The remaining functions are for input
        validation, or wrappers around commands that are run by clicking the
        button controls.
        """
        title_string = ' '.join(["ODK Tools GUI", __version__])
        master.title(title_string)
        label_width = 20
        textbox_width = 85
        output_height = 25
        xlsx_browse = {'filetypes': (('Excel Spreadsheet File', '.xlsx'),)}
        xml_browse = {'filetypes': (('XForm XML File', '.xml'),)}
        exe_browse = {'filetypes': (('Exe File', '.exe'),)}
        jar_browse = {'filetypes': (('Java Jar File', '.jar'),)}

        font = ('Arial', 8)
        ttk.Style().configure('.', font=font)

        master.xlsform_path, xlsform_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XLSForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.xform_out_path, xform_out_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="XForm output path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xml_browse)
        master.generate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate XForm", label_width=label_width,
            command=lambda: ODKToolsGui.generate_xform(
                master=master, xlsform_path=xlsform_path,
                xform_path=xform_out_path))

        master.sep0 = ttk.Separator(master=master).grid(sticky="we")

        master.xform_in_path, xform_in_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xml_browse)
        master.java_path, java_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="Java path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=exe_browse)
        master.validate_path, validate_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="ODK_Validate path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=jar_browse)
        master.validate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Validate XForm", label_width=label_width,
            command=lambda: ODKToolsGui.validate_xform(
                master=master, java_path=java_path, validate_path=validate_path,
                xform_path=xform_in_path))

        master.sep1 = ttk.Separator(master=master).grid(sticky="we")

        master.xlsform_path_images, xlsform_path_images = \
            ODKToolsGui.build_path_frame(
                master=master,
                label_text="* XLSForm path", label_width=label_width,
                textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.generate_images = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Images", label_width=label_width,
            command=lambda: ODKToolsGui.generate_images(
                master=master,
                xlsform_path=xlsform_path_images))

        master.sep2 = ttk.Separator(master=master).grid(sticky="we")

        master.xform_sl_path, xform_sl_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xml_browse)
        master.sitelangs_path, sitelangs_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* Site Languages path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.z7zip_path, z7zip_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="7zip path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=exe_browse)
        master.generate_editions = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Editions", label_width=label_width,
            command=lambda: ODKToolsGui.generate_editions(
                master=master, xform_path=xform_sl_path,
                sitelangs_path=sitelangs_path, z7zip_path=z7zip_path))

        master.sep3 = ttk.Separator(master=master).grid(sticky="we")

        master.output = ttk.Frame(master=master, height=10)
        master.output.grid(sticky='w')
        master.output.rowconfigure(index=0, pad=10, weight=1)

        master.output.row_label = ttk.Label(
            master=master.output, text="Last run output",
            width=label_width)
        master.output.row_label.grid(row=0, column=0, padx=5, sticky="w")

        master.output.textbox = tkinter.Text(
            master=master.output, width=textbox_width+10, height=output_height)
        master.output.textbox.config(wrap='word', font=font)
        master.output.textbox.grid(row=0, column=1, padx=5, columnspan=2)

        master.output.scroll = ttk.Scrollbar(
            master=master.output, command=master.output.textbox.yview)
        master.output.scroll.grid(row=0, column=3, padx=5, pady=5, sticky='ns')
        master.output.textbox['yscrollcommand'] = master.output.scroll.set

    @staticmethod
    def build_action_frame(master, label_text, label_width, command):
        """
        Generate a frame with a button for executing a command.

        The frame contains a grid row, with 3 columns: a label and a button
        labelled "Run" which executes the command on click.

        The command / function passed in should be a lambda which doesn't
        return or require any input parameters; in the above layout code the
        examples bake in a reference to the relevant variable (bound to a
        control) which is used to run the function.

        Parameters.
        :param master: tk.Frame. The parent of the generated frame.
        :param label_text: str. The text to display next to the command button.
        :param label_width: int. How wide the label should be.
        :param command: function. What to do when the button is clicked.
        :return: path frame (tk Frame), path variable (tk StringVar)
        """
        frame = ttk.Frame(master=master)
        frame.grid(sticky='w')
        frame.rowconfigure(index=0, pad=10, weight=1)

        frame.row_label = ttk.Label(
            master=frame, text=label_text, width=label_width)
        frame.row_label.grid(row=0, column=0, padx=5, sticky="w")

        frame.button = ttk.Button(master=frame, text="Run", command=command)
        frame.button.grid(row=0, column=1, padx=5)
        return frame

    @staticmethod
    def build_path_frame(
            master, label_text, label_width, textbox_width, browser_kw):
        """
        Generate a frame with controls for collecting a file path.

        The frame contains a grid row, with 3 columns: a label, a text box,
        and a button which opens the file explorer which can be used to
        select the file path visually.

        Parameters.
        :param master: tk.Frame. The parent of the generated frame.
        :param label_text: str. The text to display next to the path textbox.
        :param label_width: int. How wide the label should be.
        :param textbox_width: int. How wide the text box should be.
        :param browser_kw: dict. Keyword arguments to pass to the file browser.
        :return: path frame (tk Frame), path variable (tk StringVar)
        """
        frame = ttk.Frame(master=master)
        frame.grid()
        frame.rowconfigure(index=0, pad=10, weight=1)

        frame.row_label = ttk.Label(
            master=frame, text=label_text, width=label_width)
        frame.row_label.grid(row=0, column=0, padx=5, sticky="w")

        path = tkinter.StringVar()
        frame.textbox = ttk.Entry(
            master=frame, textvariable=path, width=textbox_width)
        frame.textbox.grid(row=0, column=1, padx=5, columnspan=2)

        frame.browse = ttk.Button(
            master=frame, text="Browse...",
            command=lambda: ODKToolsGui.file_browser(
                browser_kw=browser_kw, target_variable=path))
        frame.browse.grid(row=0, column=3, padx=5)
        return frame, path

    @staticmethod
    def file_browser(browser_kw, target_variable):
        """
        Set the target_variable value using a file chooser dialog.

        Parameters.
        :param browser_kw: dict. Passed in to filedialog constructor.
        :param target_variable: tk control. Where should the value be placed.
        """
        target_variable.set(tkinter.filedialog.askopenfilename(**browser_kw))

    @staticmethod
    def _validate_path(variable_name, path):
        """
        Check if the supplied path is not empty and corresponds to a file.

        If either check fails, launch a message box which states the error.

        Parameters.
        :param variable_name: str. Name of variable to state in error messages.
        :param path: str. Path to check.
        :return: valid (bool) does the path appear to be valid.
        """
        valid = False
        if path is None:
            path = ""

        if len(path) == 0:
            input_error = (
                "{0} is empty. Please either:".format(variable_name),
                "- Enter the path, or",
                "- Select the path using the 'Browse...' button.")
            tkinter.messagebox.showerror(
                title="Input Error",
                message="\n".join(input_error))
        elif not os.path.isfile(path.strip('"')):
            file_error = (
                "{0} does not correspond to a file.".format(variable_name),
                "Please check the path and try again.")
            tkinter.messagebox.showerror(
                title="File Error",
                message="\n".join(file_error))
        else:
            valid = True
        return valid

    @staticmethod
    def _get_same_xlsform_name(xlsform_path):
        """
        Generate a name for an XForm using the path and name of an XLSForm.

        Parameters.
        :param xlsform_path: str. Path to XLSForm to use.
        return: str. Path for XForm XML file output.
        """
        xlsform_dir = os.path.dirname(xlsform_path)
        xlsform_name = os.path.basename(xlsform_path)
        xform_name = xlsform_name.replace(".xlsx", ".xml")
        xform_path = os.path.join(xlsform_dir, xform_name)
        return xform_path

    @staticmethod
    def _run_generate_xform(xlsform_path, xform_path):
        """
        Return XLS2XForm result, including any generated warnings.

        Calls xls2xform_convert using the supplied xlsform_path.
        - XLSForm path is always required.
        - If xform_path is blank, use the XLSForm filename and path.

        If any of the paths end up not being resolved, error message boxes are
        opened to indicate this clearly to the user.

        Parameters.
        :param xlsform_path: str. Path to XLSForm to convert.
        :param xform_path: str. Path for XForm XML output.
        :return: tuple (output header message, message content)
        """
        valid_xlsform = ODKToolsGui._validate_path("XLSForm path", xlsform_path)

        if len(xform_path) == 0:
            xform_path = ODKToolsGui._get_same_xlsform_name(
                xlsform_path=xlsform_path)

        if valid_xlsform and xform_path is not None:
            unquoted_xlsform = xlsform_path.strip('"')
            unquoted_xform = xform_path.strip('"')
            header = "XLS2XForm was run. Output below."
            try:
                content = xls2xform_convert(
                    xlsform_path=unquoted_xlsform,
                    xform_path=unquoted_xform,
                    validate=False)
                content.append(ODKToolsGui._xform_empty_question_label_patch(
                    unquoted_xform))
            except PyXFormError as error:
                content = [str(error)]
        else:
            header = "XLS2XForm not run: invalid arguments."
            content = None

        return header, content

    @staticmethod
    def _xform_empty_question_label_patch(xform_path):
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
        status = ""
        try:
            with open(xform_path, mode='r') as xform_file:
                xform_content = xform_file.read()
            xform_fixed, status = ODKToolsGui.\
                _xform_empty_question_label_patch_content(xform_content)
            xform_fixed_xml = xmltodict.unparse(xform_fixed)
            with open(xform_path, mode='w') as fixed:
                fixed.write(xform_fixed_xml)
        except OSError as ose:
            status = str(ose)
        return status

    @staticmethod
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
        xml_dict = xmltodict.parse(xform_content, force_list=force_list)
        xml_model = xml_dict["h:html"]["h:head"]["model"]
        for bound_item in xml_model["bind"]:
            for translation in xml_model["itext"]["translation"]:
                for itext_item in translation["text"]:
                    bound_item_ref = "{0}:label".format(bound_item["@nodeset"])
                    itext_ref_match = itext_item["@id"] == bound_item_ref
                    itext_item_value = itext_item.get("value")
                    has_plain_text_value = any(
                        isinstance(x, str) for x in itext_item_value)
                    if itext_ref_match and not has_plain_text_value:
                        itext_item_value.append("&nbsp;")
                        status_message = "Added itext value patch (&nbsp; fix)."
        return xml_dict, status_message

    @staticmethod
    def generate_xform(master, xlsform_path, xform_path):
        """
        Run the XForm generator, clear the textbox and insert the output.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xlsform_path: str. Path to XLSForm to convert.
        :param xform_path: str. Path for XForm XML output.
        """
        header, content = ODKToolsGui._run_generate_xform(
            xlsform_path=xlsform_path.get(),
            xform_path=xform_path.get())
        text = ODKToolsGui._format_output(header=header, content=content)
        master.output.textbox.delete("1.0", tkinter.END)
        master.output.textbox.insert(tkinter.END, text)

    @staticmethod
    def _run_generate_images(xlsform_path):
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
        valid_xlsform = ODKToolsGui._validate_path("XLSForm path", xlsform_path)

        if valid_xlsform:
            unquoted_xlsform = xlsform_path.strip('"')
            header = "Generate Images was run. Output below."
            images_log = logging.getLogger('odk_tools.question_images.images')
            images_log.setLevel("DEBUG")
            log_capture = _CapturingHandler(logger=images_log)
            content = log_capture.watcher.output
            images.write_images(xlsform_path=unquoted_xlsform)
        else:
            header = "Generate Images not run: invalid arguments."
            content = None

        return header, content

    @staticmethod
    def generate_images(master, xlsform_path):
        """
        Run the images generator, clear the textbox and insert the output.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xlsform_path: str. Path to XLSForm to convert.
        """
        header, content = ODKToolsGui._run_generate_images(
            xlsform_path=xlsform_path.get())
        text = ODKToolsGui._format_output(header=header, content=content)
        master.output.textbox.delete("1.0", tkinter.END)
        master.output.textbox.insert(tkinter.END, text)

    @staticmethod
    def _current_directory():
        """
        Get the path to the current executing file.

        As a script, __file__ works, but as a frozen / pyinstaller exe, the
        sys.executable is required to get the right path.

        Adapted from http://stackoverflow.com/a/404750.

        :return: str. Path to currently executing script / executable.
        """
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(__file__)
        return application_path

    @staticmethod
    def _popen_kwargs():
        """Common keyword arguments for subprocess.Popen."""
        return {'universal_newlines': True,
                'cwd': os.path.expanduser("~"),
                'stdin': subprocess.PIPE,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE}

    @staticmethod
    def _is_java_callable(popen_kwargs):
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
        return found, path

    @staticmethod
    def _locate_odk_validate(current_directory):
        """
        Check if ODK_Validate is in the current directory.

        :return: str. Absolute path to "ODK_Validate.jar".
        """
        odk_validate_path = None
        local_validate = os.path.join(current_directory, 'ODK_Validate.jar')
        if os.path.isfile(local_validate):
            odk_validate_path = os.path.normpath(local_validate)
        return odk_validate_path

    @staticmethod
    def _run_validate_xform(java_path, validate_path, xform_path):
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
        popen_kwargs = ODKToolsGui._popen_kwargs()
        if len(java_path) == 0:
            valid_java, java_path = ODKToolsGui._is_java_callable(
                popen_kwargs=popen_kwargs)
        else:
            valid_java = ODKToolsGui._validate_path("Java path", java_path)

        if len(validate_path) == 0:
            current_directory = ODKToolsGui._current_directory()
            validate_path = ODKToolsGui._locate_odk_validate(
                current_directory=current_directory)
        valid_validate = ODKToolsGui._validate_path(
            "ODK_Validate path", validate_path)

        valid_xform = ODKToolsGui._validate_path(
            "XForm path", xform_path)

        if valid_java and valid_validate and valid_xform:
            unquoted_validate = validate_path.strip('"')
            unquoted_xform = xform_path.strip('"')
            cmd = ['java', '-jar', unquoted_validate, unquoted_xform]
            env = {'PATH': java_path}
            header = "Validate was run. Output below."
            with subprocess.Popen(cmd, env=env, **popen_kwargs) as p:
                content = [p.stderr.read(), p.stdout.read()]
        else:
            header = "Validate not run: invalid arguments."
            content = None

        return header, content

    @staticmethod
    def _format_output(header, content):
        """
        Return the formatted header and content, in this case line separated.
        """
        return "\n\n".join([header, *content])

    @staticmethod
    def validate_xform(master, java_path, validate_path, xform_path):
        """
        Run the XForm validation, clear the textbox and insert the output.
        """
        header, content = ODKToolsGui._run_validate_xform(
            java_path=java_path.get(),
            validate_path=validate_path.get(),
            xform_path=xform_path.get())
        text = ODKToolsGui._format_output(header=header, content=content)
        master.output.textbox.delete("1.0", tkinter.END)
        master.output.textbox.insert(tkinter.END, text)

    @staticmethod
    def _is_7zip_callable(popen_kwargs):
        """
        Check if 7zip can be invoked, and return the exec path.

        On Windows, assume 64-bit Program Files. Otherwise, assume it's on PATH.

        Parameters.
        :param popen_kwargs: dict. Options to pass through to subprocess.Popen.
        :return: bool (working java -version), str (path to java)
        """
        if os.name == "nt":
            path = "C:/Program Files/7-zip/7z"
        else:
            path = "7z"
        cmd = "{0} -version".format(path)
        with subprocess.Popen(cmd, **popen_kwargs) as p:
            output = p.stdout.read()
        found = output.startswith('\n7-Zip')
        return found, path

    @staticmethod
    def _run_generate_editions(xform_path, sitelangs_path, z7zip_path=''):
        """
        Return edition generation result, including any stderr / stdout content.

        If the paths is not resolved, error message boxes are opened to
        indicate this clearly to the user.

        Parameters.
        :param xform_path: str. Path to XLSForm to convert.
        :param sitelangs_path: str. Path to site languages spreadsheet.
        :param z7zip_path: str. Optional path to 7zip.
        :return: tuple (output header message, message content)
        """
        valid_xform = ODKToolsGui._validate_path("XLSForm path", xform_path)
        valid_sitelang = ODKToolsGui._validate_path(
            "Site Languages path", sitelangs_path)

        if len(z7zip_path) == 0:
            valid_z7zip, z7zip_path = ODKToolsGui._is_7zip_callable(
                popen_kwargs=ODKToolsGui._popen_kwargs())
        else:
            valid_z7zip = ODKToolsGui._validate_path("7zip path", z7zip_path)

        if valid_xform and valid_sitelang and valid_z7zip:
            unquoted_xform = xform_path.strip('"')
            unquoted_sitelang = sitelangs_path.strip('"')
            header = "Generate Editions was run. Output below."
            editions_log = logging.getLogger(
                'odk_tools.language_editions.editions')
            editions_log.setLevel('DEBUG')
            log_capture = _CapturingHandler(logger=editions_log)
            content = log_capture.watcher.output
            editions.write_editions(xform_path=unquoted_xform,
                                    site_languages=unquoted_sitelang,
                                    z7zip_path=z7zip_path)
        else:
            header = "Generate Editions not run: invalid arguments."
            content = None

        return header, content

    @staticmethod
    def generate_editions(master, xform_path, sitelangs_path, z7zip_path):
        """
        Run the editions generator, clear the textbox and insert the output.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xform_path: str. Path to XLSForm to convert.
        :param sitelangs_path: str. Path to site languages spreadsheet.
        :param z7zip_path: str. Optional path to 7zip.
        """
        header, content = ODKToolsGui._run_generate_editions(
            xform_path=xform_path.get(), sitelangs_path=sitelangs_path.get(),
            z7zip_path=z7zip_path.get())
        text = ODKToolsGui._format_output(header=header, content=content)
        master.output.textbox.delete("1.0", tkinter.END)
        master.output.textbox.insert(tkinter.END, text)


if __name__ == "__main__":
    root = tkinter.Tk()
    my_gui = ODKToolsGui(root)
    root.mainloop()
