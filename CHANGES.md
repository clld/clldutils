# Changes

## 3.21.0

- Fixed a bug whereby thesis types were not linearized according to the Unified
  stylesheet in `clldutils.Source.text`.
- Added support for serializing Source objects as Markdown text.
- Added Python 3.12 to supported versions.


## 3.20.0

Dropped py3.7 compatibility.

Added functionality to insert text into markdown documents.


## 3.19.2

Package SIL's Charis TrueType fonts with `clldutils` for convenient access
e.g. from tools such as `xhtml2pdf`.


## 3.18.2

Fixed `clldutils.markup.Table` such that it actually outputs "proper" TSV when
rendering with `tablefmt="tsv"`.


## 3.18.1

Fixed a bug in `oaipmh` whereby OAI-PMH requests with resumptionToken would fail.


## 3.18.0

More versatile geocoords-to-string conversion in `clldutils.coordinates`.


## 3.17.0

- Vendor `paginate` package as `clldutils.paginate`, because the former has seen
  no release since 2016.
- Vendor `webhelpers2.html` package as `clldutils.html`, because the former has seen
  no release since 2015.
- Remove dependency on `csvw` for CSV reading in `iso_639_3`.


## 3.16.1

- Fixed bug whereby a missing command was **not** reported properly in the error message.


## 3.16.0

- Documentation overhaul.


## 3.15.1

- Fixed bug whereby OAI-PMH responses without resumption token would raise an error.


## 3.15.0

- Support for simple OAI-PMH harvesting.


## 3.14.0

- Better markdown link detection (on demand).


## 3.13.0

- Add functionality to strip TeX markup when instantiating a `Source` object.
- Allow passing keyword arguments through to `Source` from factory method `from_entry`.


## 3.12.0

- Added `clldutils.path.ensure_cmd` and `clldutils.text.replace_pattern`.
- Dropped support for py3.6.


## 3.11.1

- Fixed bug whereby a character preceding a markdown link would be stripped
  when applying `MarkdownLink.replace`.


## 3.11.0

- Added support for manipulation of links in markdown text.


## 3.10.1

- Fixed bug whereby brackets with the same start and closing token would
  lead to errors in `clldutils.text`.


## 3.10.0

- Added `clilib.add_random_seed`


## 3.9.0

- Added `clilib.add_csv_field_size_limit`
- Added API docs (via sphinx + readthedocs)


## 3.8.0

- Extended support for markdown parsing


## 3.7.0

- Dropped support for py35
- Fixed support for reading ISO 639-3 data


## 3.6.0

Support for reading tables in markdown text, e.g. to parse CONTRIBUTORS.md.


## 3.5.4

Fixes missing linearization of edition in Source instances.


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

