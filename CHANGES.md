# Changes

## [unreleased]


## 2.8.0

Added modules to manage color in visualizations and create simple svg graphics.
Fixed several bugs.


## 2.7.0

Added a method to make sure the repos accessed by an API is checked out
to a release tag.


## 2.6.3

Upgrade configparser requirement to work with Anaconda.


## 2.6.2

Fixed a bug where an app would not open in the browser.


## 2.6.1

Make import of pathlib or pathlib2 only depend on the python version and
not on whether pathlib2 is installed or not.


## 2.6.0

Support for initializing clldutils.source.Source objects from pybtex.database.Entry.


## 2.5.2

- added a tiny bit of functionality to support formatted docstrings
  for clilib.command


## 2.5.1

- fixed a couple DeprecationWarnings


## 2.5.0

- add support for ordered updates of JSON files.


## 2.4.1

- avoid attrs DeprecationWarning (see https://github.com/python-attrs/attrs/issues/307)


## 2.4.0

- Added support for easily creating data URIs.
- Deprecated `cached_property`.


## 2.3.0

Now with license texts for most common licenses.


## 2.2.0

Support for retrieving data from re-arranged ISO 639-3 site.


## 2.0.1

Added back in backwards compatibility for the dsv functionality.


## 2.0.0

Removed 
- module testing: Equivalent functiuonality is available for testing with pytest,
  in particular the `tmpdir` and `capsys` fixtures.
- `clldutils.misc.normalize_name` and modules dsv and csvw: 
  Use the package csvw instead, which provides the identical API.

