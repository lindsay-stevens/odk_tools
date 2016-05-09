import tkinter
import tkinter.filedialog
import tkinter.messagebox
from tkinter import ttk
import os
import sys
import subprocess


class ODKToolsGui:

    def __init__(self, master=None):

        master.title("ODK Tools GUI")
        label_width = 20
        textbox_width = 75
        output_height = 25
        xlsx_browse = {'filetypes': (('Excel XLSX Spreadsheet File', '.xlsx'),)}
        xml_browse = {'filetypes': (('XForm XML File', '.xml'),)}
        exe_browse = {'filetypes': (('Java Exe File', '.exe'),)}
        jar_browse = {'filetypes': (('Java Jar File', '.jar'),)}

        font = ('Arial', 9)
        ttk.Style().configure('.', font=font)

        master.xlsform_path, xlsform_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XLSForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.generate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate XForm", label_width=label_width,
            command=lambda: ODKToolsGui.generate_xform(
                xlsform_path=xlsform_path))
        master.generate_images = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Images", label_width=label_width,
            command=lambda: ODKToolsGui.generate_images(
                xlsform_path=xlsform_path))

        master.sep1 = ttk.Separator(master=master).grid(sticky="we")

        master.java_path, java_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="Java path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=exe_browse)
        master.validate_path, validate_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="ODK_Validate path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=jar_browse)
        master.xform_path, xform_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xml_browse)
        master.validate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Validate XForm", label_width=label_width,
            command=lambda: ODKToolsGui.validate_xform(
                master=master, java_path=java_path, validate_path=validate_path,
                xform_path=xform_path))

        master.sep2 = ttk.Separator(master=master).grid(sticky="we")

        master.xlsform_sl_path, xlsform_sl_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XLSForm path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.sitelangs_path, sitelangs_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* Site Languages path", label_width=label_width,
            textbox_width=textbox_width, browser_kw=xlsx_browse)
        master.generate_editions = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Editions", label_width=label_width,
            command=lambda: ODKToolsGui.generate_editions(
                xlsform_path=xlsform_sl_path, sitelangs_path=sitelangs_path))

        master.sep3 = ttk.Separator(master=master).grid(sticky="we")

        master.output = ttk.Frame(master=master, height=10)
        master.output.grid(sticky='w')
        master.output.rowconfigure(index=0, pad=10, weight=1)

        master.output.row_label = ttk.Label(
            master=master.output, text="Last run output",
            width=label_width)
        master.output.row_label.grid(row=0, column=0, padx=5, sticky="w")

        master.output.textbox = tkinter.Text(
            master=master.output, width=textbox_width-10, height=output_height)
        master.output.textbox.config(wrap='word', font=font)
        master.output.textbox.grid(row=0, column=1, padx=5, columnspan=2)

        master.output.scroll = ttk.Scrollbar(
            master=master.output, command=master.output.textbox.yview)
        master.output.scroll.grid(row=0, column=3, padx=5, pady=5, sticky='ns')
        master.output.textbox['yscrollcommand'] = master.output.scroll.set

    @staticmethod
    def build_action_frame(master, label_text, label_width, command):
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
        and a

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
        strip_quotes = path.strip('"')
        if len(path) == 0:
            input_error = (
                "{0} is empty. Please either:".format(variable_name),
                "- Enter the path, or",
                "- Select the path using the 'Browse...' button.")
            tkinter.messagebox.showerror(
                title="Input Error",
                message="\n".join(input_error))
        elif not os.path.isfile(strip_quotes):
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
    def _ensure_quoted(path):
        if not path.startswith('"'):
            path = '"{0}'.format(path)
        if not path.endswith('"'):
            path = '{0}"'.format(path)
        return path

    @staticmethod
    def generate_xform(xlsform_path):
        xlsform = xlsform_path.get()
        valid_xlsform = ODKToolsGui._validate_path("XLSForm path", xlsform)
        if valid_xlsform:
            quoted_xlsform = ODKToolsGui._ensure_quoted(xlsform)

    @staticmethod
    def generate_images(xlsform_path):
        xlsform = xlsform_path.get()
        valid_xlsform = ODKToolsGui._validate_path("XLSForm path", xlsform)
        if valid_xlsform:
            quoted_xlsform = ODKToolsGui._ensure_quoted(xlsform)

    @staticmethod
    def _current_directory():
        """http://stackoverflow.com/a/404750"""
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(__file__)
        return application_path

    @staticmethod
    def popen_kwargs():
        return {'universal_newlines': True,
                'cwd': os.path.expanduser("~"),
                'stdin': subprocess.PIPE,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE}

    @staticmethod
    def locate_java():
        popen_kws = ODKToolsGui.popen_kwargs()
        java_path = None
        with subprocess.Popen(['where', 'java'], **popen_kws) as p:
            stdout_result = p.stdout.read()
        for candidate in stdout_result.split('\n'):
            if os.path.isfile(candidate) and candidate.endswith('java.exe'):
                java_path = candidate
        return java_path

    @staticmethod
    def locate_odk_validate():
        odk_validate_path = None
        current_dir = ODKToolsGui._current_directory()
        local_validate = os.path.join(current_dir, 'ODK_Validate.jar')
        if os.path.isfile(local_validate):
            odk_validate_path = os.path.normpath(local_validate)
        return odk_validate_path

    @staticmethod
    def validate_xform(master, java_path, validate_path, xform_path):

        java_path_str = java_path.get()
        if len(java_path_str) == 0:
            java_path_str = ODKToolsGui.locate_java()
        valid_java = ODKToolsGui._validate_path("Java path", java_path_str)

        validate_path_str = validate_path.get()
        if len(validate_path_str) == 0:
            validate_path_str = ODKToolsGui.locate_odk_validate()
        valid_validate = ODKToolsGui._validate_path(
            "ODK_Validate path", validate_path_str)

        xform = xform_path.get()
        valid_xform = ODKToolsGui._validate_path("XForm path", xform)

        if valid_java and valid_validate and valid_xform:
            quoted_validate = validate_path_str.strip('"')
            quoted_xform = xform.strip('"')
            popen_kws = ODKToolsGui.popen_kwargs()
            popen_args = ['java', '-jar', quoted_validate, quoted_xform]
            print(popen_args)
            with subprocess.Popen(popen_args, **popen_kws,
                                  env={'PATH': java_path_str}) as p:
                master.output.textbox.insert(tkinter.END, p.stderr.read())
                master.output.textbox.insert(tkinter.END, p.stdout.read())

    @staticmethod
    def generate_editions(xlsform_path, sitelangs_path):
        print('generate editions at', xlsform_path.get(), sitelangs_path.get())


root = tkinter.Tk()
my_gui = ODKToolsGui(root)
root.mainloop()