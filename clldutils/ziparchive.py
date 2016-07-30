# coding: utf8
from __future__ import unicode_literals, print_function, division
from zipfile import ZipFile, ZIP_DEFLATED
from io import TextIOWrapper

from six import binary_type

from clldutils.path import as_posix


class ZipArchive(ZipFile):
    def __init__(self, fname, mode='r'):
        ZipFile.__init__(
            self, as_posix(fname), mode=mode, compression=ZIP_DEFLATED, allowZip64=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_text(self, name):
        if name in self.namelist():
            return TextIOWrapper(self.open(name), encoding='utf-8-sig').read()

    def write_text(self, text, name):
        if not isinstance(text, binary_type):
            text = text.encode('utf8')
        self.writestr(name, text)
