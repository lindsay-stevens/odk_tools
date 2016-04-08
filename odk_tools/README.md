# Tools for working with ODK XLSforms
The following modules are included, details on each are in the following
sections:
- question_images
- language_editions
- conversion_to_docx

The scripts for question images and language editions are compatible with
`pyinstaller script.py --onefile`, for easy distribution to other users.

Ideally this project will incorporate the XLS2XForm library so the complete
workflow from design to deployment is included, for example:
- xls2xform: convert XLSX form design spreadsheet to xform XML.
- question_images: generate question images from XLSX form design.
- language_editions: prepare site-specific language editions as zip files, from
  the xform XML, question images, and a list of sites and languages.

## Question Images
Purpose:

The ODK Collect app for Android does not have a capability for styling text,
and just presents the text plainly. This script creates images for itext that
are displayed for each question.

Function:

The script relies on the presence of extended, optional metadata added to an
XLSForm to generate images containing question and hint text. An example of
this is in the test folder for language_editions (TODO: proper spec).

Usage:
The standard '-h' flag will show parameter information and usage.
```shell
images.py XFORM_NAME.xlsx
```

Output:

A folder named 'XFORM_NAME-media' (name matching the input file), created in
the same directory as the input xform file.


## Language Editions
Purpose:

A XLSForm may be used to prepare a questionnaire for many languages, but it may
be preferable / required to only provide the languages that will be used by the
site.

So that it is possible to maintain just one XLSForm, this script reads creates
"editions" that contain only the itext elements and images for the required
languages.

So that the files can be easily distributed, the files for each site are
archived in .zip files.

Additionally, the script will attempt to append the site code to a xform item
named 'SID', which is assumed to be the subject ID. This is so that the default
value is, for example, '1309-61202-', instead of just '1309-'.


Function:

The script requires an XForm, a XForm-media folder, a XLSX sheet that describes
which sites require which languages, and the path to a 7zip executable. An
example of this is in the test folder for language_editions (TODO: proper spec).

Usage:
The standard '-h' flag will show parameter information and usage.
```shell
editions.py XFORM.xml site_langs.xlsx
```

Output:

A folder named 'editions' in the same folder as the input xform file,
containing a zip archive for each site, containing the modified xform file
and itext images.


## Conversion to docx
Purpose:

An work in progress / experiment that is intended to generate a MS Word / docx
document version of a XLSForm. The document could be used as a printable paper
backup copy of the questionnaire, in case the tablet is lost or unavailable.
