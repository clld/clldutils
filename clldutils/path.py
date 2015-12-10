# coding: utf8
from __future__ import unicode_literals
import os
import shutil

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


def remove(p):
    os.remove(as_posix(p))


def rmtree(p, **kw):
    return shutil.rmtree(as_posix(p), **kw)


def move(src, dst):
    return shutil.move(as_posix(src), as_posix(dst))


def copy(src, dst):
    return shutil.copy(as_posix(src), as_posix(dst))


def copytree(src, dst, **kw):
    return shutil.copytree(as_posix(src), as_posix(dst), **kw)
