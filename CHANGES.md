# Changes

## 2.0.1

Added back in backwards compatibility for the dsv functionality.


## 2.0.0

Removed 
- module testing: Equivalent functiuonality is available for testing with pytest,
  in particular the `tmpdir` and `capsys` fixtures.
- `clldutils.misc.normalize_name` and modules dsv and csvw: 
  Use the package csvw instead, which provides the identical API.

