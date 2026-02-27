"""
This module provides utilities for filesystem paths and files.

.. note::

    Most of the original rationale for this module has been rendered moot by recent changes in
    stdlib, making `pathlib.Path` the default format for function arguments that represent paths.
"""
import os
import sys
import mmap
import types
import shutil
import hashlib
import pathlib
import tempfile
import importlib
import contextlib
import subprocess
import unicodedata
from typing import Union, Optional, Literal
from collections.abc import Generator, Iterable

__all__ = [
    'ensure_cmd', 'sys_path', 'memorymapped', 'import_module',
    'readlines', 'walk', 'md5', 'Manifest', 'git_describe', 'TemporaryDirectory',
]

Path = pathlib.Path  # keep for backwards compatibility.
PathType = Union[str, pathlib.Path]


def ensure_cmd(cmd: str, **kw) -> str:
    """
    Make sure an executable is installed and return its full path.

    Just a wrapper around `shutil.which` which raises a useful exception when the command
    is not installed.
    """
    cmd_ = shutil.which(cmd, **kw)
    if not cmd_:
        raise ValueError(f'The command {cmd} must be installed!')
    return cmd_


@contextlib.contextmanager
def sys_path(p: PathType):
    """
    Context manager providing a context with path `p` appended to `sys.path`.

    .. seealso:: :func:`import_module`
    """
    sys.path.insert(0, str(Path(p)))
    yield
    sys.path.pop(0)


@contextlib.contextmanager
def memorymapped(filename: PathType, access=mmap.ACCESS_READ) -> Generator[mmap.mmap, None, None]:
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


def import_module(p: PathType) -> types.ModuleType:
    """
    Import a python module from anywhere in the filesystem.
    """
    p = Path(p)
    with sys_path(p.parent):
        m = importlib.import_module(p.stem)
        if Path(m.__file__).parent not in [p.parent, p]:
            # If we end up importing from the wrong place, raise an error:
            raise ImportError(m.__file__)  # pragma: no cover
        return m


def as_posix(p) -> str:
    """Used as one way to get a string representation of a Path."""
    if hasattr(p, 'as_posix'):
        return p.as_posix()
    if isinstance(p, str):
        return Path(p).as_posix()
    raise ValueError(p)


def readlines(  # pylint: disable=R0917,R0913
        p: Union[PathType, Iterable[str]],
        encoding: Optional[str] = None,
        strip: bool = False,
        comment: Optional[str] = None,
        normalize: Optional[Literal["NFC", "NFD", "NFKC", "NFKD"]] = None,
        linenumbers: bool = False,
) -> list[Union[tuple[int, str], str]]:
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
    res = []
    try:
        with Path(p).open(encoding=encoding or 'utf-8') as fp:
            res = fp.readlines()
    except TypeError:
        res = [line.decode(encoding) if encoding else line for line in p]

    if strip:
        res = [line.strip() or None for line in res]
    if comment:
        res = [None if line and line.startswith(comment) else line for line in res]
    if normalize:
        res = [unicodedata.normalize(normalize, line) if line else line for line in res]
    if linenumbers:
        return list(enumerate(res, start=1))
    return [line for line in res if line is not None]


def walk(
        p: PathType,
        mode: Literal["all", "files", "dirs"] = 'all',
        **kw
) -> Generator[pathlib.Path, None, None]:
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


def md5(p: PathType, bufsize: int = 32768) -> str:
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
    def from_dir(cls, d: PathType, relative_to: PathType = None) -> 'Manifest':
        """Creates Manifest for all files in d."""
        d = Path(d)
        assert d.is_dir()
        return cls((str(p.relative_to(relative_to or d)), md5(p)) for p in walk(d, mode='files'))

    def __str__(self):
        return '\n'.join(f'{v}  {k}' for k, v in sorted(self.items()))

    def write(self, outdir: Optional[PathType] = None):
        """Write manifest to a directory."""
        Path(outdir or '.').joinpath('manifest-md5.txt').write_text(f'{self}', encoding='utf8')


def git_describe(dir_: PathType, git_command='git') -> str:
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
        f"--git-dir={dir_.joinpath('.git')}", 'describe', '--always', '--tags']
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise ValueError(stderr)
            res = stdout.strip()  # pragma: no cover
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
