# coding: utf8
from __future__ import unicode_literals

from six import PY3, string_types


if PY3:  # pragma: no cover
    import pathlib
else:
    import pathlib2 as pathlib

Path = pathlib.Path


def as_posix(p):
    if isinstance(p, Path):
        return p.as_posix()
    if isinstance(p, string_types):
        return Path(p).as_posix()
    raise ValueError(p)
