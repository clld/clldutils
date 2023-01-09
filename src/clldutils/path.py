"""
This module provides utilities for filesystem paths and files.

.. note::

    Most of the original rationale for this module has been rendered moot by recent changes in
    stdlib, making `pathlib.Path` the default format for function arguments that represent paths.
"""
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
import typing
import unicodedata

from clldutils.misc import deprecated

__all__ = [
    'ensure_cmd', 'sys_path', 'memorymapped', 'import_module',
    'readlines', 'move', 'walk', 'md5', 'Manifest', 'git_describe', 'TemporaryDirectory',
]

Path = pathlib.Path  # keep for backwards compatibility.


def ensure_cmd(cmd, **kw) -> str:
    """
    Make sure an executable is installed and return its full path.

    Just a wrapper around `shutil.which` which raises a useful exception when the command
    is not installed.
    """
    cmd_ = shutil.which(cmd, **kw)
    if not cmd_:
        raise ValueError('The command {} must be installed!'.format(cmd))
    return cmd_


@contextlib.contextmanager
def sys_path(p):
    """
    Context manager providing a context with path `p` appended to `sys.path`.

    .. seealso:: :func:`import_module`
    """
    sys.path.insert(0, str(Path(p)))
    yield
    sys.path.pop(0)


@contextlib.contextmanager
def memorymapped(filename: typing.Union[str, pathlib.Path], access=mmap.ACCESS_READ) -> mmap.mmap:
    """
    Context manager to access a memory mapped file.

    .. seealso:: `<https://docs.python.org/3/library/mmap.html>`_
    """
    f = Path(filename).open('rb')
    try:
        m = mmap.mmap(f.fileno(), 0, access=access)
        try:
            yield m
        finally:
            m.close()
    finally:
        f.close()


def import_module(p: pathlib.Path) -> type(os):
    """
    Import a python module from anywhere in the filesystem.
    """
    with sys_path(p.parent):
        m = importlib.import_module(p.stem)
        if Path(m.__file__).parent not in [p.parent, p]:
            # If we end up importing from the wrong place, raise an error:
            raise ImportError(m.__file__)  # pragma: no cover
        return m


def path_component(s, encoding='utf-8'):
    deprecated('With PY3 path components are always `str`')
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


def readlines(p: typing.Union[pathlib.Path, str, list, tuple],
              encoding: typing.Optional[str] = None,
              strip: bool = False,
              comment: typing.Optional[str] = None,
              normalize: typing.Optional[str] = None,
              linenumbers: bool = False) \
        -> typing.List[typing.Union[typing.Tuple[int, str], str]]:
    """
    Read a `list` of lines from a text file (or iterable of lines).

    :param p: File path (or `list` or `tuple` of text)
    :param encoding: Registered codec.
    :param strip: If `True`, strip leading and trailing whitespace.
    :param comment: String used as syntax to mark comment lines. When not `None`, \
    commented lines will be stripped. This implies `strip=True`.
    :param normalize: Do UNICODE normalization ('NFC', 'NFKC', 'NFD', 'NFKD')
    :param linenumbers: return also line numbers.
    :return: `list` of text lines or pairs (`int`, text or `None`).
    """
    if comment:
        strip = True
    if isinstance(p, (list, tuple)):
        res = [line.decode(encoding) if encoding else line for line in p]
    else:
        with Path(p).open(encoding=encoding or 'utf-8') as fp:
            res = fp.readlines()
    if strip:
        res = [line.strip() or None for line in res]
    if comment:
        res = [None if line and line.startswith(comment) else line for line in res]
    if normalize:
        res = [unicodedata.normalize(normalize, line) if line else line for line in res]
    if linenumbers:
        return [(n, line) for n, line in enumerate(res, start=1)]
    return [line for line in res if line is not None]


def rmtree(p, **kw):
    deprecated("Use of deprecated function rmtree! Use shutil.rmtree instead.")
    return shutil.rmtree(p, **kw)


def move(src, dst):
    """
    Functionality of `shutil.move` accepting `pathlib.Path` as input.

    .. seealso:: `<https://bugs.python.org/issue39140>`_
    """
    return shutil.move(str(src), str(dst))


def copy(src, dst):
    deprecated("Use of deprecated function copy! Use shutil.copy instead.")
    return shutil.copy(src, dst)


def copytree(src, dst, **kw):
    deprecated("Use of deprecated function copytree! Use shutil.copytree instead.")
    return shutil.copytree(src, dst, **kw)


def walk(p, mode='all', **kw) -> typing.Generator[pathlib.Path, None, None]:
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


def md5(p: typing.Union[pathlib.Path, str], bufsize: int = 32768) -> str:
    """
    Compute md5 sum of the content of a file.
    """
    hash_md5 = hashlib.md5()
    with Path(p).open('rb') as fp:
        for chunk in iter(lambda: fp.read(bufsize), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class Manifest(dict):
    """A `dict` mapping relative path names to md5 sums of file contents.

    A `str(Manifest.from_dir(d, relative_to=d.parent))` is equivalent
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
    """
    Run `git describe --always --tags` on a directory.

    .. note:: `git_command` must be in the PATH and is called in a subprocess.
    """
    dir_ = Path(dir_)
    if not dir_.exists():
        raise ValueError('cannot describe non-existent directory')
    dir_ = dir_.resolve()
    cmd = [
        ensure_cmd(git_command),
        '--git-dir=%s' % dir_.joinpath('.git'), 'describe', '--always', '--tags']
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
    """
    `tempfile.TemporaryDirectory`, but yielding a `pathlib.Path`
    """
    def __enter__(self) -> pathlib.Path:
        return Path(self.name)
