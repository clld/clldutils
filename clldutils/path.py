# coding: utf8
from __future__ import unicode_literals
import os
import sys
import shutil
import tempfile
import subprocess
import hashlib
from contextlib import contextmanager
import importlib

from six import PY3, string_types, binary_type, text_type


if PY3:  # pragma: no cover
    import pathlib
else:
    import pathlib2 as pathlib

Path = pathlib.Path


@contextmanager
def sys_path(p):
    p = Path(p).as_posix()
    sys.path.append(p)
    yield
    if sys.path[-1] == p:
        sys.path.pop()


def import_module(p):
    with sys_path(p.parent):
        return importlib.import_module(p.stem)


# In python 3, pathlib treats path components and string-like representations or
# attributes of paths (like name and stem) as unicode strings. Unfortunately this is not
# true for pathlib under python 2.7. So as workaround for the case of using non-ASCII
# path names with python 2.7 the following two wrapper functions are provided.
# Note that the issue is even more complex, because pathlib with python 2.7 under windows
# may still pose problems.
def path_component(s, encoding='utf8'):
    if isinstance(s, binary_type) and PY3:  # pragma: no cover
        s = s.decode(encoding)
    if isinstance(s, text_type) and not PY3:
        s = s.encode(encoding)
    return s


def as_unicode(p, encoding='utf8'):
    if PY3:  # pragma: no cover
        return '%s' % p
    return (b'%s' % p).decode(encoding)


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


def md5(p):
    hash_md5 = hashlib.md5()
    with open(Path(p).as_posix(), "rb") as fp:
        for chunk in iter(lambda: fp.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


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
    if not isinstance(res, text_type):
        res = res.decode('utf8')
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
