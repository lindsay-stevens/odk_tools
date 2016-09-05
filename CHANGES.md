# Changelog


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