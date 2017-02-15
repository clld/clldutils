# coding: utf8
"""
A python2+3 compatible INI object.
"""
from __future__ import unicode_literals
import re

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

    def gettext(self, section, option, whitespace_preserving_prefix='.'):
        """
        While configparser supports multiline values, it does this at the expense of
        stripping leading whitespace for each line in such a value. Sometimes we want
        to preserve such whitespace, e.g. to be able to put markdown with nested lists
        into INI files. We support this be introducing a special prefix, which is
        prepended to lines starting with whitespace in `settext` and stripped in
        `gettext`.
        """
        lines = []
        for line in self.get(section, option, fallback='').split('\n'):
            if re.match(re.escape(whitespace_preserving_prefix) + '\s+', line):
                line = line[len(whitespace_preserving_prefix):]
            lines.append(line)
        return '\n'.join(lines)

    def settext(self, section, option, value, whitespace_preserving_prefix='.'):
        lines = []
        for line in value.split('\n'):
            if re.match('\s+', line):
                line = whitespace_preserving_prefix + line
            lines.append(line)
        self.set(section, option, '\n'.join(lines))

    def write(self, fname, **kw):
        if not isinstance(fname, Path):
            fname = Path(fname)
        with fname.open('w', encoding='utf8') as fp:
            fp.write(self.write_string(**kw))
