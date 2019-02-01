import sys

if sys.version_info < (3, 5):  # pragma: no cover
    import pathlib2 as pathlib
else:
    import pathlib

assert pathlib
