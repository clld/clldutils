"""
This module provides an enhanced `INI format <https://en.wikipedia.org/wiki/INI_file>`_ reader and
writer based on the standard library's
`configparser <https://docs.python.org/3/library/configparser.html>`_ .
"""
import io
import re
import pathlib
from typing import Union, Any
import configparser
from collections.abc import Iterable

DOT = '.'


class INI(configparser.ConfigParser):
    """
    An enhanced `ConfigParser` with better support for list-valued options and multiline text.
    """
    @staticmethod
    def format_list(items: Iterable[str]) -> str:
        """Concatenate items as INI style list."""
        return ''.join('\n' + item for item in items)

    @classmethod
    def from_file(cls, fname: Union[str, pathlib.Path], encoding='utf-8', **kw) -> 'INI':
        """
        `kw` are passed through to `ConfigParser.__init__`.
        """
        obj = cls(**kw)
        obj.read(str(fname), encoding=encoding)
        return obj

    def write_string(self, **kw) -> str:
        """Write the INI prefixed with an encoding comment suitable for emacs."""
        res = io.StringIO()
        res.write('# -*- coding: utf-8 -*-\n')
        super().write(res, **kw)
        return res.getvalue()

    def set(self, section: str, option: str, value: Union[None, list, tuple, Any] = None):
        """
        Enhances `ConfigParser.set` by

        - ignoring `None` values
        - creating missing sections
        - accepting `list` instances as value
        """
        if value is None:
            return
        if not self.has_section(section):
            self.add_section(section)
        if isinstance(value, (list, tuple)):
            value = self.format_list(value)
        elif not isinstance(value, str):
            value = f'{value}'
        super().set(section, option, value)

    def getlist(self, section: str, option: str) -> list:
        """Get section content as list."""
        return self.get(section, option, fallback='').strip().splitlines()

    def gettext(self, section, option, whitespace_preserving_prefix=DOT) -> str:
        """
        While configparser supports multiline values, it does this at the expense of
        stripping leading whitespace for each line in such a value. Sometimes we want
        to preserve such whitespace, e.g. to be able to put markdown with nested lists
        into INI files. We support this be introducing a special prefix, which is
        prepended to lines starting with whitespace in :meth:`INI.settext` and stripped in
        :meth:`INI.gettext` .
        """
        lines = []
        for line in self.get(section, option, fallback='').splitlines():
            if re.match(re.escape(whitespace_preserving_prefix) + r'\s+', line):
                line = line[len(whitespace_preserving_prefix):]
            lines.append(line)
        return '\n'.join(lines)

    def settext(self, section: str, option: str, value: str, whitespace_preserving_prefix=DOT):
        """
        Set a text option, preserving newlines.
        """
        lines = []
        for line in value.splitlines():
            if re.match(r'\s+', line):
                # The line starts with whitespace, so we have to add a non-whitespace char to
                # preserve it.
                line = whitespace_preserving_prefix + line
            lines.append(line)
        self.set(section, option, '\n'.join(lines))

    def write(self, fname, **kw):  # pylint: disable=arguments-differ
        """
        Write an INI file.
        """
        pathlib.Path(fname).write_text(self.write_string(**kw), encoding='utf-8')
