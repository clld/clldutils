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
import unicodedata
import mmap

from six import PY3, string_types, binary_type, text_type

from clldutils.misc import UnicodeMixin

if PY3:  # pragma: no cover
    import pathlib
else:
    import pathlib2 as pathlib

Path = pathlib.Path


@contextmanager
def sys_path(p):
    p = Path(p).as_posix()
    sys.path.insert(0, p)
    yield
    sys.path.pop(0)


@contextmanager
def memorymapped(filename, access=mmap.ACCESS_READ):
    fd = open(as_posix(filename))
    try:
        m = mmap.mmap(fd.fileno(), 0, access=access)
    except:  # pragma: no cover
        fd.close()
        raise
    try:
        yield m
    finally:
        m.close()
        fd.close()


def import_module(p):
    with sys_path(p.parent):
        m = importlib.import_module(p.stem)
        if Path(m.__file__).parent not in [p.parent, p]:
            # If we end up importing from the wrong place, raise an error:
            raise ImportError(m.__file__)  # pragma: no cover
        return m


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


def read_text(p, encoding='utf8', **kw):
    with Path(p).open(encoding=encoding, **kw) as fp:
        return fp.read()


def write_text(p, text, encoding='utf8', **kw):
    with Path(p).open('w', encoding=encoding, **kw) as fp:
        return fp.write(text)


def readlines(p,
              encoding=None,
              strip=False,
              comment=None,
              normalize=None,
              linenumbers=False):
    """
    Read a `list` of lines from a text file.

    :param p: File path (or `list` or `tuple` of text)
    :param encoding: Registered codec.
    :param strip: If `True`, strip leading and trailing whitespace.
    :param comment: String used as syntax to mark comment lines. When not `None`, \
    commented lines will be stripped. This implies `strip=True`.
    :param normalize: 'NFC', 'NFKC', 'NFD', 'NFKD'
    :param linenumbers: return also line numbers.
    :return: `list` of text lines or pairs (`int`, text or `None`).
    """
    if comment:
        strip = True
    if isinstance(p, (list, tuple)):
        res = [l.decode(encoding) if encoding else l for l in p]
    else:
        with Path(p).open(encoding=encoding or 'utf8') as fp:
            res = fp.readlines()
    if strip:
        res = [l.strip() or None for l in res]
    if comment:
        res = [None if l and l.startswith(comment) else l for l in res]
    if normalize:
        res = [unicodedata.normalize(normalize, l) if l else l for l in res]
    if linenumbers:
        return [(n + 1, l) for n, l in enumerate(res)]
    return [l for l in res if l is not None]


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


class Manifest(dict, UnicodeMixin):
    """
    A `dict` mapping relative path names to md5 sums of file contents.

    A `Manifest.from_dir(d, relative_to=d.parent).__unicode__()` is equivalent
    to the content of the file `manifest-md5.txt` of the BagIt specification.

    .. seealso:: https://en.wikipedia.org/wiki/BagIt
    """
    def __unicode__(self):
        return '\n'.join('{0}  {1}'.format(v, k) for k, v in sorted(self.items()))

    def write(self, outdir=None):
        write_text(Path(outdir or '.').joinpath('manifest-md5.txt'), '{0}'.format(self))

    @classmethod
    def from_dir(cls, d, relative_to=None):
        d = Path(d)
        assert d.is_dir()
        return cls({p.relative_to(relative_to or d).as_posix(): md5(p)
                    for p in walk(d, mode='files')})


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
