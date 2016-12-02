import odk_tools


class Preferences:
    """Preferences for the GUI."""
    app_title = ' '.join(["ODK Tools GUI", odk_tools.__version__])
    label_width = 20
    textbox_width = 85
    output_height = 25
    xlsx_browse = {'filetypes': (('Excel Spreadsheet File', '.xlsx'),)}
    xml_browse = {'filetypes': (('XForm XML File', '.xml'),)}
    exe_browse = {'filetypes': (('Exe File', '.exe'),)}
    jar_browse = {'filetypes': (('Java Jar File', '.jar'),)}
    settings_browse = {'filetypes': (('Collect Settings File', '.settings'),)}
    generic_pre_msg = "{0} task initiated, please wait...\n\n"
    font = ('Arial', 8)
