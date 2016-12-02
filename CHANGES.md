# Changelog


## 2016.11
- Removed the option to specify XForm output path for Generate XForm task path. I hardly ever use it and it's always going to the same location with the same name but as XML, so that behaviour is now locked in
- After a successful run of the Generate XForm task, the relevant XForm and XLSForm paths will be copied down in to the input boxes for the other tasks, assuming that they're going to be done in sequence anyway
- Change the input validation behaviour from using a pop-up message box to instead use the output textbox, so that all feedback uses the same mechanism
- Update the user guide to match the above interface and behavioural changes
- Big code restructure to untangle the parts that create the GUI from the parts that manage running the tasks, to make it easier to work with and to test. In particular, splitting off the validation parts means that all the path validation is in a separate module, so the previous gui tests that were essentially permutations on path validation are not needed.


## 2016.10
- Technical stuff related to 2016.9 issues with PIL. Changed the way that image tests evaluate whether the produced image is the same as the reference image, so that it tolerates a very small amount of practically imperceptible (and seemingly random) variability.


## 2016.9
- Fix validation of the "collect.settings" parameter for the "generate editions" task. This was missing steps used on all other path inputs that strip invalid characters around the path, like double quotes or whitespace.
- Related to the above, add a missing test and remove an unnecessary conversion of the path to an absolute path.
- Improve user feedback by making it so that when the "Run" button is pressed, the message indicating that the task was started is displayed in the main textbox before any work on that task is started. Previously, this was shown after the task was completed, which is kind of pointless.
- Related to testing "generate images", the latest PIL version produces images that have an extremely small difference to the reference images. The difference is about 6 pixels that are off by less than 10 percent shading around some of the black text. It is not clear why this is so, but the images are still valid. Instead of doing fuzzy matching, the reference images were updated.
- Dependencies: freeze these to specific versions, and switch from my pyxform fork to the master since my updates were merged recently.


## 2016.8
- Fix unicode characters being mangled by the XForm patch step: by not 
  specifying the file encoding on file access, this broke the output of 
  unicode characters.
- Improved user feedback: add a message in the output area to indicate which 
  action is currently running, and also catch all exceptions and show the 
  message in case something goes wrong. Previously, it was very mysterious 
  when an uncaught exception happened.
- Add input validation of paths to language_editions: check that at least 
  the file extensions look right.
- Expand the characters that the gui input processing will trim: previously it 
  would just remove quotes around paths, now it will remove spaces, tabs, 
  carriage returns, line feeds and quotes.


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