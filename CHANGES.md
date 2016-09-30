# Changelog

## 2016.7
- Remove dependency on 7-zip in editions generator. It turned out that the 
  Python built-in zipfile is just as quick when using 'deflate' compression, 
  which seems to do about the same job on images as the slower 'lzma'.
- Re-write editions generator processes to take advantage of Python zipfile 
  ability to specify archive file paths, which vastly simplifies the module by 
  removing the need for copying files to the desired folder structure. 7-zip 
  only has a facility for renaming archive paths after creation, and it's only 
  possible to rename one file at a time.
- Remove concurrency option from editions.py since it's not possible (or at 
  least, apparently inadvisable) to do use Python's zipfile concurrently.
- Include typing annotations in editions.py to eliminate need for some tests.
- Add ability to include an ODK Collect app "collect.settings" file in a 
  language editions zip file.
- Silence argument parser warnings in parser tests by re-directing stderr.
- Update GUI code, tests and screenshot to match updated interface for the editions 
  module.


## 2016.6
- Add option to XForms editions generator to nest the output inside of folders 
  "odk/forms" to allow extracting the archive from the root device storage 
  folder.


## 2016.5
- Change XForms editions generator to put files into a zip named with just the 
  site code instead of XForm name plus site code. This makes it possible / 
  easier to prepare multiple forms in one zip for each site.


## 2016.4
- Fix detection of whether there's an existing plain text question label.
- Don't try to unpack the task result content if there isn't anything to unpack.


## 2016.3
- Update dependencies for pyxform and xmltodict to forks which address issues 
  found in the 2016.2 patch updates, namely:
    - pyxform: avoid escaping double quotes in text (so it's same as xmltodict; 
      due to using xml.dom.minidom vs. expat or lxml)
    - xmltodict: preserve the output of mixed child elements, otherwise the 
      order of items within groups of html:body to not match the instance order, 
      which in turn caused ODK Collect to not function properly.
- General note: if the GitHub-based dependencies are not being recognised by 
  PyCharm, make sure that "pip" and "setuptools" are up to date.


## 2016.2
- Add a hopefully temporary patch / fix for an Android ODK Collect issue
  present in v1.4.10_rev_1061, where a question with no plain text label can
  cause the app to crash. The fix involves adding a default plain text label if
  none exists, using the invisible HTML non-blank-space character "&nbsp;".
- Update versions of requirements, and tweak tests accordingly since recent PIL
  broke some reference image comparison tests.
- Change file name chooser dialog type used for the XForm conversion XML file
  path to the type for saving files. All other file name choosers are the type
  for opening files.
- Fix handling of XLSForm conversion warning messages if the input form
  definition has hard errors. This used to just fail silently and mysteriously;
  now the error message/s are displayed in the output pane.


## 2016.1
- Initial release.