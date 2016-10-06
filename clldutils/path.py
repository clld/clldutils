# coding: utf8
from __future__ import unicode_literals
import os
import shutil
import tempfile
import subprocess

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


def walk(p, mode='all', **kw):
    """
    Wrapper for `os.walk`, yielding `Path` objects.

    :param p: root of the directory tree to walk.
    :param mode: 'all|dirs|files', defaulting to 'all'.
    :param kw: Keyword arguments are passed to `os.walk`.
    :return: Generator for the requested Path objects.
    """
    for dirpath, dirnames, filenames in os.walk(as_posix(p), **kw):
        if mode in ['all', 'dirs']:
            for dirname in dirnames:
                yield Path(dirpath).joinpath(dirname)
        if mode in ['all', 'files']:
            for fname in filenames:
                yield Path(dirpath).joinpath(fname)


def git_describe(dir_):
    dir_ = Path(dir_)
    if not dir_.exists():
        raise ValueError('cannot describe non-existent directory')
    dir_ = dir_.resolve()
    cmd = [
        'git', '--git-dir=%s' % dir_.joinpath('.git').as_posix(), 'describe', '--always']
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            res = stdout.strip()  # pragma: no cover
        else:
            raise ValueError(stderr)
    except ValueError:
        res = dir_.name
    return res


class TemporaryDirectory(object):
    """
    A trimmed down backport of python 3's tempfile.TemporaryDirectory.
    """
    def __init__(self, **kw):
        self.name = Path(tempfile.mkdtemp(**kw))

    def __enter__(self):
        return self.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        rmtree(self.name)
