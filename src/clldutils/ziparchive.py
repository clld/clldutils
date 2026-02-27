"""
A zipFile subclass with better support for reading and writing text.
"""
import io
import zipfile
from typing import Optional, Union

from .path import PathType


class ZipArchive(zipfile.ZipFile):
    """A ZipFile subclass with better support for reading and writing text files."""
    _init_defaults = {
        'compression': zipfile.ZIP_DEFLATED,
        'allowZip64': True,
    }

    def __init__(self, fname: PathType, mode='r', **kwargs):
        for k, v in self._init_defaults.items():
            kwargs.setdefault(k, v)
        super().__init__(str(fname), mode=mode, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_text(self, name: str, encoding='utf-8-sig') -> Optional[str]:
        """Read a named archive member as str."""
        if name in self.namelist():
            return io.TextIOWrapper(self.open(name), encoding=encoding).read()
        return None  # pragma: no cover

    def write_text(self, text: Union[str, bytes], name: str, _encoding='utf-8'):
        """Write text to a named archive member."""
        if not isinstance(text, bytes):
            text = text.encode(_encoding)
        self.writestr(name, text)
