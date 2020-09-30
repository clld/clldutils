# Changes

## [unreleased]


## 3.5.3

Fixes issue where current ISO 639-3 code tables could not be parsed.


## 3.5.2

Added `attrlib.cmp_off` to support writing compatible code using attrs
without deprecation warnings.


## 3.5.1

Fixes bug where SFM markers were interpreted to narrowly.


## 3.5.0

Added `clilib.PathType`


## 3.4.0

Support for basic dataset metadata reading and writing, integrated with API.


## 3.3.0

High-level support for database management.


## 3.2.1

Bugfix to make apilib compatible with new-style cli.


## 3.2.0

- https://github.com/clld/clldutils/issues/87
- https://github.com/clld/clldutils/issues/88
- https://github.com/clld/clldutils/issues/89


## 3.1.2

Bugfix release


## 3.1.1

Bugfix release


## 3.1.0

- Support for converting geo coordinates to "human readable" notation.
- Support for cli using proper argparse subparsers.


## 3.0.1

Fixes the wheel distribution which included the obsolete dsv module.


## 3.0.0

- dropped support for py < 3.5 (in particular, py2.7 is no longer supported)
- removed already deprecated clldutils.misc.cached_property
- removed legacy module clldutils.dsv
- deprected a couple of functions which are (almost) aliases of stdlib functionality
  for py > 3.4.


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

