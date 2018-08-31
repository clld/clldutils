# Changes

## [unreleased]


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

