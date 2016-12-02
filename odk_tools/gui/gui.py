import tkinter
import tkinter.filedialog
import tkinter.messagebox
from functools import partial
from tkinter import ttk
from odk_tools.gui.wrappers import generate_images, generate_xform, \
    validate_xform, generate_editions
from odk_tools.gui import preferences


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
        prefs = preferences.Preferences()
        master.title(prefs.app_title)
        ttk.Style().configure('.', font=prefs.font)
        ODKToolsGui.build_generate_xform(master=master, prefs=prefs)
        ODKToolsGui.build_validate_xform(master=master, prefs=prefs)
        ODKToolsGui.build_generate_images(master=master, prefs=prefs)
        ODKToolsGui.build_generate_editions(master=master, prefs=prefs)
        ODKToolsGui.build_output_box(master=master, prefs=prefs)

    @staticmethod
    def build_generate_xform(master, prefs):
        """Setup for the Generate XForm task widgets."""
        master.xlsform_path, xlsform_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XLSForm path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.xlsx_browse)
        master.generate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate XForm", label_width=prefs.label_width,
            command=lambda: ODKToolsGui.generate_xform(
                master=master, xlsform_path=xlsform_path),
            pre_msg=prefs.generic_pre_msg.format("Generate XForm"))

    @staticmethod
    def build_validate_xform(master, prefs):
        """Setup for the Validate XForm task widgets."""
        master.sep0 = ttk.Separator(master=master).grid(sticky="we")

        master.xform_in_path, xform_in_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XForm path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.xml_browse)
        master.java_path, java_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="Java path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.exe_browse)
        master.validate_path, validate_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="ODK_Validate path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.jar_browse)
        master.validate_xform = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Validate XForm", label_width=prefs.label_width,
            command=lambda: ODKToolsGui.validate_xform(
                master=master, java_path=java_path, validate_path=validate_path,
                xform_path=xform_in_path),
            pre_msg=prefs.generic_pre_msg.format("Validate XForm"))

    @staticmethod
    def build_generate_images(master, prefs):
        """Setup for the Generate Images task widgets."""
        master.sep1 = ttk.Separator(master=master).grid(sticky="we")

        master.xlsform_path_images, xlsform_path_images = \
            ODKToolsGui.build_path_frame(
                master=master,
                label_text="* XLSForm path", label_width=prefs.label_width,
                textbox_width=prefs.textbox_width, browser_kw=prefs.xlsx_browse)
        master.generate_images = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Images", label_width=prefs.label_width,
            command=lambda: ODKToolsGui.generate_images(
                master=master, xlsform_path=xlsform_path_images),
            pre_msg=prefs.generic_pre_msg.format("Generate Images"))

    @staticmethod
    def build_generate_editions(master, prefs):
        """Setup for the Generate Editions task widgets."""
        master.sep2 = ttk.Separator(master=master).grid(sticky="we")

        master.xform_sl_path, xform_sl_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* XForm path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.xml_browse)
        master.sitelangs_path, sitelangs_path = ODKToolsGui.build_path_frame(
            master=master,
            label_text="* Site Languages path", label_width=prefs.label_width,
            textbox_width=prefs.textbox_width, browser_kw=prefs.xlsx_browse)
        master.collect_settings, collect_settings = \
            ODKToolsGui.build_path_frame(
                master=master,
                label_text="Collect Settings path",
                label_width=prefs.label_width,
                textbox_width=prefs.textbox_width,
                browser_kw=prefs.settings_browse)
        nest_in_odk_folders = tkinter.IntVar()
        master.generate_editions = ODKToolsGui.build_action_frame(
            master=master,
            label_text="Generate Editions", label_width=prefs.label_width,
            command=lambda: ODKToolsGui.generate_editions(
                master=master, xform_path=xform_sl_path,
                sitelangs_path=sitelangs_path,
                collect_settings=collect_settings,
                nest_in_odk_folders=nest_in_odk_folders),
            pre_msg=prefs.generic_pre_msg.format("Generate Editions"))
        master.nest_in_odk_folders = ttk.Checkbutton(
            master=master.generate_editions, variable=nest_in_odk_folders,
            text="Nest output in 'odk/forms/*'")
        master.nest_in_odk_folders.grid(row=0, column=2, padx=5)

        master.sep3 = ttk.Separator(master=master).grid(sticky="we")

        master.output = ttk.Frame(master=master, height=10)
        master.output.grid(sticky='w')
        master.output.rowconfigure(index=0, pad=10, weight=1)

    @staticmethod
    def build_output_box(master, prefs):
        """Setup for the task results output box."""
        master.output.row_label = ttk.Label(
            master=master.output, text="Last run output",
            width=prefs.label_width)
        master.output.row_label.grid(row=0, column=0, padx=5, sticky="w")

        master.output.textbox = tkinter.Text(
            master=master.output, width=prefs.textbox_width+10,
            height=prefs.output_height)
        master.output.textbox.config(wrap='word', font=prefs.font)
        master.output.textbox.grid(row=0, column=1, padx=5, columnspan=2)
        master.output.scroll = ttk.Scrollbar(
            master=master.output, command=master.output.textbox.yview)
        master.output.scroll.grid(row=0, column=3, padx=5, pady=5, sticky='ns')
        master.output.textbox['yscrollcommand'] = master.output.scroll.set

    @staticmethod
    def textbox_pre_message(event, message):
        """Clear the output Text field and insert the provided message."""
        event.widget.master.master.output.textbox.delete("1.0", tkinter.END)
        event.widget.master.master.output.textbox.insert(tkinter.END, message)

    @staticmethod
    def build_action_frame(master, label_text, label_width, command,
                           pre_msg=None):
        """
        Generate a frame with a button for executing a command.

        The frame contains a grid row, with 3 columns: a label and a button
        labelled "Run" which executes the command on click.

        The command / function passed in should be a lambda which doesn't
        return or require any input parameters; in the above layout code the
        examples bake in a reference to the relevant variable (bound to a
        control) which is used to run the function.

        So that the user is notified that the task connected to the "Run"
        button has started, once the ButtonPress event fires, the specified
        pre_msg is displayed in the main output textbox. The button's command
        is implicitly attached to the subsequent ButtonRelease event. Refs:
        - http://tcl.tk/man/tcl8.5/TkCmd/bind.htm#M7
        - http://tcl.tk/man/tcl8.5/TkCmd/button.htm#M5

        Parameters.
        :param master: tk.Frame. The parent of the generated frame.
        :param label_text: str. The text to display next to the command button.
        :param label_width: int. How wide the label should be.
        :param command: function. What to do when the button is clicked.
        :param pre_msg: str. Message to display in textbox on button press.
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
        if pre_msg is not None:
            frame.button.bind(
                sequence="<ButtonPress>", add='+',
                func=partial(ODKToolsGui.textbox_pre_message, message=pre_msg))
        return frame

    @staticmethod
    def build_path_frame(
            master, label_text, label_width, textbox_width, browser_kw,
            dialog_function=tkinter.filedialog.askopenfilename):
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
        :param dialog_function: File dialog generation function to use.
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
                browser_kw=browser_kw, target_variable=path,
                dialog_function=dialog_function))
        frame.browse.grid(row=0, column=3, padx=5)
        return frame, path

    @staticmethod
    def file_browser(browser_kw, target_variable, dialog_function):
        """
        Set the target_variable value using a file chooser dialog.

        Parameters.
        :param browser_kw: dict. Passed in to filedialog constructor.
        :param target_variable: tk control. Where should the value be placed.
        :param dialog_function: function to generate the file dialog control.
        """
        target_variable.set(dialog_function(**browser_kw))

    @staticmethod
    def textbox_replace(tk_end, widget, new_text):
        """
        Clear a textbox widget and insert the new text.

        Important! This is specific to "Entry" widgets, for which the start
        index is specified as 0. For "Text" widgets, the start index is instead
        in the form of "row.col" e.g. delete("1.0", END).

        :param tk_end: the tkinter.END constant meaning the final textbox char.
        :param widget: reference to the widget to work with.
        :param new_text: text to insert into the widget.
        :return: None
        """
        if len(widget.get()) != 0:
            widget.delete(0, tk_end)
        widget.insert(tk_end, new_text)

    @staticmethod
    def generate_xform(master, xlsform_path):
        """
        Run the XForm generator, and put the result in the main textbox.

        If the task was run, copy the parameters down into the other task
        path input text boxes. The XForm file is saved adjacent to the XLSForm,
        with the same name except with an XML extension.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xlsform_path: str. Path to XLSForm to convert.
        """
        result, xform_path_used, xlsform_path_used = generate_xform.wrapper(
            xlsform_path=xlsform_path.get())
        master.output.textbox.insert(tkinter.END, result)
        if xform_path_used is not None:
            tk_end = tkinter.END
            updates = [(master.xlsform_path.textbox, xlsform_path_used),
                       (master.xform_in_path.textbox, xform_path_used),
                       (master.xlsform_path_images.textbox, xlsform_path_used),
                       (master.xform_sl_path.textbox, xform_path_used)]
            for w, t in updates:
                ODKToolsGui.textbox_replace(tk_end=tk_end, widget=w, new_text=t)

    @staticmethod
    def generate_images(master, xlsform_path):
        """
        Run the images generator, and put the result in the main textbox.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xlsform_path: str. Path to XLSForm to convert.
        """
        result = generate_images.wrapper(
            xlsform_path=xlsform_path.get())
        master.output.textbox.insert(tkinter.END, result)

    @staticmethod
    def validate_xform(master, java_path, validate_path, xform_path):
        """
        Run the XForm validation, and put the result in the main textbox.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param java_path: str. Optional path to java.exe, otherwise this is
          looked for in the envar JAVA_HOME.
        :param validate_path: str. Optional path to ODK_Validate.jar. This is
          packaged with the GUI but maybe a different version is desired.
        :param xform_path: str. Path to XLSForm to convert.
        """
        result = validate_xform.wrapper(
                java_path=java_path.get(),
                validate_path=validate_path.get(),
                xform_path=xform_path.get())
        master.output.textbox.insert(tkinter.END, result)

    @staticmethod
    def generate_editions(master, xform_path, sitelangs_path, collect_settings,
                          nest_in_odk_folders):
        """
        Run the editions generator, and put the result in the main textbox.

        Parameters.
        :param master: tkinter.Frame. Frame where master.output.textbox is.
        :param xform_path: str. Path to XLSForm to convert.
        :param sitelangs_path: str. Path to site languages spreadsheet.
        :param nest_in_odk_folders: int. 1=yes, 0=no. Nest in /odk/forms/*.
        :param collect_settings: str. Optional path to collect.settings file.
        """
        result = generate_editions.wrapper(
                xform_path=xform_path.get(),
                sitelangs_path=sitelangs_path.get(),
                collect_settings=collect_settings.get(),
                nest_in_odk_folders=nest_in_odk_folders.get())
        master.output.textbox.insert(tkinter.END, result)


if __name__ == "__main__":
    root = tkinter.Tk()
    my_gui = ODKToolsGui(root)
    root.mainloop()
