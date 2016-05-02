# XLSForm Images Extension Specification
This document describes extensions to the XLSForm specification that
are required to use the image generation script in this package.

The modifications affect the "survey" sheet, and require the addition of a
sheet named "image_settings". The changes / content to these sheets are
described in the following sections. The workbook should therefore contain
the following sheets:
- survey
- choices
- settings
- image_settings

These extensions are compatible with the existing XLSForm specifications, and
the xls2xform tools.

There is some trial and error required to ensure that the various combinations
of settings, text and images results in a generated image that displays all
content within the image dimensions legibly and aesthetically.


## Text Handling


### Alignment
Text is written to the image center-aligned.


### Printable Characters
The only limitation on what characters can be written to an image is whether
the character exists in the desired font. For example, some Unicode
characters may not appear in the regular Arial font, but may be in Arial
Unicode font.


### Characters Per Line
The maximum amount of text to be written per line is configurable in the image
settings. If text is longer than that maximum, the text is split into multiple
lines. If this maximum results in text outside of the width of the image, a
warning is displayed in the script console.


### Punctuation
In order to provide a more easily readable text layout, the script will
insert an extra newline after '.', '?' and '!', unless they are at the end of
the text string. 'Extra newline' means stop the current line and leave one
blank before continuing the remaining text, if any.

Frequently, these punctuation characters mark the end of a sentence, and
frequently, multi-sentence questions have some repetitive component that is
easier to identify if it is on a different line. Since English does not adhere
to regular patterns it's not possible to reliably identify sentence termination
punctuation. Even with a library like NLTK there is some room for error.

A downside to this behaviour is that the text 'e.g. apples' would be broken
into 3 lines containing 'e.', 'g.', 'apples'. Alternatives like writing
'for example, apples', or 'eg, apples' can be used instead.

An upside is that no markup characters are needed, so the text can be displayed
without modification in contexts where the markup is not interpreted.


## Survey sheet
The XLSForm language suffix convention allows specifying question label, hint
image and constraint message information for each language. For example, the
following columns specify the label for 2 languages:

- label::english
- label::french
- label::german

To trigger the generation of translation data for the xform in xls2xform, the
above columns need to be present, but blank. A new column per language (using
a '#' separator instead of a '::') should contain the text to go in the image.
The xls2xform tool ignores the '#' separator columns. For example:

- label::english
- label#english
- label::french
- label#french

Label text is added to the image at the top, followed by the hint text. If a
question image is specified, it will be inserted below the hint text.

The full set of language specific columns are as follows:

- label#english
- hint#english
- image#english
- label::english
- hint::english
- image::english
- constraint_message::english


## Image Settings
The new image_settings sheet allows some customisation of the layout of the
output image. Like the 'choices' sheet, a column for each language in the
'survey' sheet should be created. The first column must contain the setting
names, subsequent columns contain the values for each language. For example:

- settings
- value::english
- value::french
- value::german

The image settings are described in the following sections. All settings are in
one continuous list in the 'image_settings' sheet, but are broken up here for
legibility.

- General image settings
- Logo settings
- Label text settings
- Hint text settings
- Nested image settings


### General Image Settings
These settings define the file names, item types, dimensions and colour of
to use for the generated image files.

- file_name_column: The column in the 'survey' sheet with name of output file.
  Generally this will be the 'name' column so that each image has the same name
  as the item it corresponds to, but it could be something else if desired.
- type_ignore_list: A comma separated list of survey item types to ignore when
  creating files. For example, 'start,end,deviceid,begin group,end group'.
- image_width: Width of output image, in pixels. If using portrait mode on the
  tablet, this should be about 90% of the resolution of the short edge of the
  tablet. For example a Nexus 9 is 2048x1536 so a good width is 1536*0.9=1382.
- image_height: Height of output image, in pixels. If using portrait mode on
  the tablet, this should be about 33% of the resolution on the long edge of
  the tablet. For example a Nexus 9 is 2048x1536 so a good width is 2048/3=683.
- image_color: The name of the colour of the image background. For example,
  'white', 'blue', 'red', etc. White blends nicely with ODK Collect.
- newline_at_question_mark: (not implemented) Option to turn on/off behaviour
  adding a newline after each question mark.


### Logo Settings
These settings define the source, placement and size of a logo image.

- logo_image_path: Path (full path, or relative to the XLSForm) to an image
  file (for example, a logo) to place at the top of every question image.
- logo_image_pixels_before: In pixels, the distance of the logo image from
  the top of the question image.
- logo_image_height: In pixels, the height of the logo image. The image will be
  resized automatically to fit this height, preserving aspect ratio, so no
  width needs to be specified.


### Label Text Settings
These settings define the source, placement, sizing, font properties and colour
of the item label text.

- text_label_column: Name of the 'survey' sheet column with the label text. If
  the corresponding value is blank for an item then no label text is included.
- text_label_pixels_before: In pixels, the distance of the beginning of the
  label text from the end of previous element (logo or image top).
- text_label_pixels_line: In pixels, the distance between lines of label text.
- text_label_wrap_char: The maximum number of characters per line in label text.
  Words are not split across lines.
- text_label_font_name: The name of the font to use for the label text. Must
  be available on the system. To find available fonts, press the Windows button,
  type 'fonts', press 'Enter'. Right click the Fonts list column area and
  choose to display the column 'Font file names'. For example 'arial.ttf' is
  regular Arial, and 'arialbd.ttf' is Arial Bold. If just a font file name is
  specified then the system font is used; alternatively the full path to a font
  file can be provided.
- text_label_font_size: In points, the size of the label text font.
- text_label_font_color: The name of the colour to use for the label text font,
  for example 'black', 'green', 'red'.


### Hint Text Settings
These settings define the source, placement, sizing, font properties and colour
of the item hint text.

- text_hint_column: Name of the 'survey' sheet column with the hint text. If
  the corresponding value is blank for an item then no hint text is included.
- text_hint_pixels_before: In pixels, the distance of the beginning of the
  hint text from the end of previous element (label, logo or image top).
- text_hint_pixels_line: In pixels, the distance between lines of hint text.
- text_hint_wrap_char: The maximum number of characters per line in hint text.
  Words are not split across lines.
- text_hint_font_name: The name of the font to use for the hint text. Details
  as per the text_label_font_name settings.
- text_hint_font_size: In points, the size of the label text font.
- text_hint_font_color: The name of the colour to use for the label text font,
  for example 'black', 'green', 'red'.


### Nested Image Settings
These settings define the source and placement of a nested image.

- nest_image_column: Name of the 'survey' sheet column with the path (full
  path, or relative to the XLSForm) to an image file (for example, a logo) to
  place at the top of every question image. If the corresponding value is blank
  for an item then no nested image is included.
- nest_image_pixels_before: In pixels, the distance of the beginning of the
  image from the end of previous element (hint, label, logo or image top).
