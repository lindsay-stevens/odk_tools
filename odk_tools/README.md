# ODK Tools

## Introduction
This package is designed with the following XForm authoring and build process
in mind:

- Design an XForm following the XLSForm standard.
- Convert the XLSForm to an XForm XML document.
- Validate the XForm document using ODK Validate.
- Generate branded images for each XForm question with a basic layout.
- Generate site-specific language editions of the XForm for deployment.

This package provides modules for:

- Generating images for each question
- Generating site-specific editions
- A GUI for users to provide parameters for the necessary scripts.

In order to generate and validate the XForm, the existing "XLSForm/pyxform"
Python library and "opendatakit/validate" Java library are bundled.

Refer to the End User Guide (GUI or CLI) for details on general usage.


## Releases
Packaging is done using PyInstaller
(```pyinstaller --onefile --windowed gui.py```), which should work cross
platform, but must be run from each platform that is being distributed to (see
the PyInstaller documentation). Documentation is converted using Pandoc
(```pandoc end_user_guide_gui.md -o end_user_guide_gui.docx```).


## Provided Modules
The following sections are describe the modules provided by this package.


### Question Images


#### Purpose
The ODK Collect app for Android has some styling capabilities based on Markdown
syntax. This came after this script was written, but it has the advantages of

- Question text doesn't have Markdown in it, so can be easily transferred to
  some other system or format without being cleaned.
- Ability to embed a logo and/or reference image beneath the question text.


#### Function
The script relies on the presence of extended, optional metadata added to an
XLSForm to generate images containing question and hint text. In the question
images folder there is:

- A specification for the required metadata (xlsform_images_spec.md).
- Two example XLSForms, one with a single language (test/Q1302_BEHAVE.xlsx) and
  one with five languages (test/Q1309_BEHAVE.xlsx).
- Example images (test/reference_images) showing a question image with a label
  only, a label and hint, and a label and a nested image, and all 3 together.


#### Usage
The standard '-h' flag will show parameter information and usage.
```shell
images.py XFORM_NAME.xlsx
```


#### Output
A folder named 'XFORM_NAME-media' (name matching the input file), created in
the same directory as the input xform file. The folder will contain an image
per question per language, according to the specified image settings.


### Language Editions


#### Purpose
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


#### Function
The script requires an XForm, a XForm-media folder, a XLSX sheet that describes
which sites require which languages, and the path to a 7zip executable. An
example of this is in the test folder for language_editions.

The "Site Languages" sheet is assumed to have the following structure. In the
first sheet, first column, from row 2 onwards, the language names for each
site separated by a forward slash, e.g. "English/Spanish/German". In the first
sheet, third column, from row 2 onwards, the site code for each site, e.g.
"61221". The specified languages must match the language names used in the
XLSForm.


#### Usage
The standard '-h' flag will show parameter information and usage.
```shell
editions.py XFORM.xml site_langs.xlsx
```

#### Output
A folder named 'editions' in the same folder as the input xform file,
containing a zip archive for each site, containing the modified xform file
and itext images.


### Conversion to docx


#### Purpose:
This is a work in progress  / experiment that is intended to generate a MS Word
 / docx document version of a XLSForm. The document could be used as a
printable paper backup copy of the questionnaire, in case the tablet is lost
or unavailable.
