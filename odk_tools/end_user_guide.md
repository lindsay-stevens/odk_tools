# ODK Tools End User Guide

## Introduction
This document is for Windows users that are responsible for designing ODK 
Collect forms, and describes how to use the tool suite for generating the 
necessary files for ODK form deployment.

## Tools
There are 4 tools in the suite currently. The list order follows the order of 
use; their names and purposes are:

- xls2xform: convert from an XLSForm design in XLSX to an ODK XForm XML file.
- ODK_Validate: simulate loading an XForm XML file in ODK Collect to see if 
  it is valid (note, the form is not displayed, just "loaded").
- images: generate images for each question in an XLSForm XLSX file.
- editions: generate site-specific zip archives using an XForm XML, images, 
  and a XLSX file specifying which languages are for which sites.

## Usage
All tools are used on the command line. To open a command prompt, press Shift 
and right click anywhere in the folder where the tools are, then choose "Open 
command window here". Tool specific instructions follow.

The file names of each tool have appended to them the first 6 characters of the 
git commit hash that the file was generated from, in order to keep track what 
it was created from.

Hint: to save typing the whole name of a file on the command line, type the 
first few letters then press Tab. If the desired file name isn’t automatically 
completed, keep pressing Tab.

Hint: to save typing the whole path to a file, press Shift, then right click on 
the desired file, then choose "Copy as path". 

## XLS2XForm
For information on parameters, type the following command:

```xls2xform.exe -h```

The command must be in the following format:

```xls2xform.exe –skip_validate input_xlsform.xlsx output_xform.xml```

For example:

```xls2xform.exe –skip_validate "\\path\to\xlsform.xlsx" "\\path\to\desired\name\xform.xml"```

The output may include some messages to indicate if the input XLSForm was valid.
These issues can be ignored, or addressed and then run the above command again.

## ODK Validate
This tool is different in that it requires Java to run. Most computers will
have Java installed; a good place to start looking is in "C:\Program Files
(x86)\Java". The full path to the "jre\bin\java.exe" is required. For example
"C:\Program Files (x86)\Java\jre1.8.0_71\bin\java.exe".

The command must be in the following format:

```java_path -jar ODK_Validate.jar input_xform.xml```

For example:

```"\\path\to\java.exe" -jar ODK_Validate.jar "\\path\to\desired\name\ xform.xml"```

As above, the output from this tool will indicate whether the form definition
is valid.

## Images
For information on parameters, type the following command:

```images.exe -h```

The command must be in the following format:

```images.exe input_xlsform.xlsx```

For example:

```images.exe "\\path\to\desired\name\xform.xml"```

This tool may take some time to run as it generates and saves images for each
question, for each language. The output folder will be in the same place as the
input XML file, and named as required by ODK Collect, e.g. XFORM-media.

This tool may output messages to indicate if there is something wrong with the
image settings specified in the XLSForm, for example if the text is too wide or
tall. The output files should be inspected manually to see if the spacing and
sizing of the text and image elements are legible. See the XLSForm images
specification for more information.

##Editions
This tool requires that 7-zip is installed on the computer. It assumes that the
7-zip program is installed at "C:\Program Files\7-zip\7z.exe". If 7-zip is not
installed in that location, the option "--zipexe" must be specified, followed
by the path to 7-zip.

For information on parameters, type the following command:

```editions.exe -h```

The command must be in the following format:

```editions.exe input_xform.xml site_languages.xlsx```

For example:

```editions.exe "\\path\to\desired\name\xform.xml" "\\path\to\site_languages.xlsx"```
