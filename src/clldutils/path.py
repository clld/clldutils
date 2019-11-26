import os
import sys
import mmap
import shutil
import hashlib
import pathlib
import tempfile
import importlib
import contextlib
import subprocess
import unicodedata

from clldutils.misc import deprecated

Path = pathlib.Path


@contextlib.contextmanager
def sys_path(p):
    sys.path.insert(0, str(Path(p)))
    yield
    sys.path.pop(0)


@contextlib.contextmanager
def memorymapped(filename, access=mmap.ACCESS_READ):
    f = Path(filename).open('rb')
    try:
        m = mmap.mmap(f.fileno(), 0, access=access)
        try:
            yield m
        finally:
            m.close()
    finally:
        f.close()


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
def path_component(s, encoding='utf-8'):
    if isinstance(s, bytes):
        s = s.decode(encoding)
    return s


def as_unicode(p, encoding='utf-8'):
    deprecated("Use of deprecated function as_unicode! Use str() instead.")
    return '%s' % p


def as_posix(p):
    if hasattr(p, 'as_posix'):
        return p.as_posix()
    elif isinstance(p, str):
        return Path(p).as_posix()
    raise ValueError(p)


def remove(p):
    deprecated('Use of deprecated function remove! Use Path.unlink instead.')
    Path(p).unlink()


def read_text(p, encoding='utf8', **kw):
    deprecated("Use of deprecated function read_text! Use Path.read_text instead.")
    with Path(p).open(encoding=encoding, **kw) as fp:
        return fp.read()


def write_text(p, text, encoding='utf8', **kw):
    deprecated("Use of deprecated function write_text! Use Path.write_text instead.")
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
        with Path(p).open(encoding=encoding or 'utf-8') as fp:
            res = fp.readlines()
    if strip:
        res = [l.strip() or None for l in res]
    if comment:
        res = [None if l and l.startswith(comment) else l for l in res]
    if normalize:
        res = [unicodedata.normalize(normalize, l) if l else l for l in res]
    if linenumbers:
        return [(n, l) for n, l in enumerate(res, 1)]
    return [l for l in res if l is not None]


def rmtree(p, **kw):
    return shutil.rmtree(str(p), **kw)


def move(src, dst):
    return shutil.move(str(src), str(dst))


def copy(src, dst):
    return shutil.copy(str(src), str(dst))


def copytree(src, dst, **kw):
    return shutil.copytree(str(src), str(dst), **kw)


def walk(p, mode='all', **kw):
    """Wrapper for `os.walk`, yielding `Path` objects.

    :param p: root of the directory tree to walk.
    :param mode: 'all|dirs|files', defaulting to 'all'.
    :param kw: Keyword arguments are passed to `os.walk`.
    :return: Generator for the requested Path objects.
    """
    for dirpath, dirnames, filenames in os.walk(str(p), **kw):
        if mode in ('all', 'dirs'):
            for dirname in dirnames:
                yield Path(dirpath).joinpath(dirname)
        if mode in ('all', 'files'):
            for fname in filenames:
                yield Path(dirpath).joinpath(fname)


def md5(p, bufsize=32768):
    hash_md5 = hashlib.md5()
    with Path(p).open('rb') as fp:
        for chunk in iter(lambda: fp.read(bufsize), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class Manifest(dict):
    """A `dict` mapping relative path names to md5 sums of file contents.

    A `Manifest.from_dir(d, relative_to=d.parent).__unicode__()` is equivalent
    to the content of the file `manifest-md5.txt` of the BagIt specification.

    .. seealso:: https://en.wikipedia.org/wiki/BagIt
    """

    @classmethod
    def from_dir(cls, d, relative_to=None):
        d = Path(d)
        assert d.is_dir()
        return cls((str(p.relative_to(relative_to or d)), md5(p)) for p in walk(d, mode='files'))

    def __str__(self):
        return '\n'.join('{0}  {1}'.format(v, k) for k, v in sorted(self.items()))

    def write(self, outdir=None):
        Path(outdir or '.').joinpath('manifest-md5.txt').write_text(
            '{0}'.format(self), encoding='utf8')


def git_describe(dir_, git_command='git'):
    dir_ = Path(dir_)
    if not dir_.exists():
        raise ValueError('cannot describe non-existent directory')
    dir_ = dir_.resolve()
    cmd = [git_command, '--git-dir=%s' % dir_.joinpath('.git'), 'describe', '--always', '--tags']
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            res = stdout.strip()  # pragma: no cover
        else:
            raise ValueError(stderr)
    except (ValueError, FileNotFoundError):
        res = dir_.name
    if not isinstance(res, str):
        res = res.decode('utf8')
    return res


class TemporaryDirectory(tempfile.TemporaryDirectory):
    def __enter__(self):
        return Path(self.name)
