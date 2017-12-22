from __future__ import unicode_literals

import io
import zipfile

from six import binary_type, iteritems

from clldutils.path import as_posix


class ZipArchive(zipfile.ZipFile):

    _init_defaults = {
        'compression': zipfile.ZIP_DEFLATED,
        'allowZip64': True,
    }

    def __init__(self, fname, mode='r', **kwargs):
        for k, v in iteritems(self._init_defaults):
            kwargs.setdefault(k, v)
        super(ZipArchive, self).__init__(as_posix(fname), mode=mode, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_text(self, name, encoding='utf-8-sig'):
        if name in self.namelist():
            return io.TextIOWrapper(self.open(name), encoding=encoding).read()

    def write_text(self, text, name, _encoding='utf-8'):
        if not isinstance(text, binary_type):
            text = text.encode(_encoding)
        self.writestr(name, text)
