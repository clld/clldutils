# coding: utf8
"""
A python2+3 compatible INI object.
"""
from __future__ import unicode_literals

from six import StringIO, string_types
from backports import configparser

from clldutils.path import Path
from clldutils.misc import nfilter


class INI(configparser.ConfigParser):
    @staticmethod
    def format_list(l):
        return ''.join('\n' + item for item in l)

    @classmethod
    def from_file(cls, fname, encoding='utf8', **kw):
        if isinstance(fname, Path):
            fname = fname.as_posix()
        obj = INI(**kw)
        obj.read(fname, encoding=encoding)
        return obj

    def write_string(self, **kw):
        res = StringIO()
        configparser.ConfigParser.write(self, res, **kw)
        res.seek(0)
        return '# -*- coding: utf-8 -*-\n' + res.read()

    def set(self, section, option, value=None):
        if value is None:
            return
        if not self.has_section(section):
            self.add_section(section)
        if isinstance(value, (list, tuple)):
            value = self.format_list(value)
        elif not isinstance(value, string_types):
            value = '%s' % value
        configparser.ConfigParser.set(self, section, option, value)

    def getlist(self, section, option):
        return nfilter(self.get(section, option, fallback='').strip().split('\n'))

    def write(self, fname, **kw):
        if not isinstance(fname, Path):
            fname = Path(fname)
        with fname.open('w', encoding='utf8') as fp:
            fp.write(self.write_string(**kw))
