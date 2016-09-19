# Changelog

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