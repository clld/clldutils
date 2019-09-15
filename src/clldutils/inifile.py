import io
import re
import pathlib
import configparser


class INI(configparser.ConfigParser):

    @staticmethod
    def format_list(l):
        return ''.join('\n' + item for item in l)

    @classmethod
    def from_file(cls, fname, encoding='utf-8', **kw):
        obj = cls(**kw)
        obj.read(str(fname), encoding=encoding)
        return obj

    def write_string(self, **kw):
        res = io.StringIO()
        res.write('# -*- coding: utf-8 -*-\n')
        super(INI, self).write(res, **kw)
        return res.getvalue()

    def set(self, section, option, value=None):
        if value is None:
            return
        if not self.has_section(section):
            self.add_section(section)
        if isinstance(value, (list, tuple)):
            value = self.format_list(value)
        elif not isinstance(value, str):
            value = '%s' % value
        super(INI, self).set(section, option, value)

    def getlist(self, section, option):
        return self.get(section, option, fallback='').strip().splitlines()

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
        for line in self.get(section, option, fallback='').splitlines():
            if re.match(re.escape(whitespace_preserving_prefix) + '\s+', line):
                line = line[len(whitespace_preserving_prefix):]
            lines.append(line)
        return '\n'.join(lines)

    def settext(self, section, option, value, whitespace_preserving_prefix='.'):
        lines = []
        for line in value.splitlines():
            if re.match('\s+', line):
                line = whitespace_preserving_prefix + line
            lines.append(line)
        self.set(section, option, '\n'.join(lines))

    def write(self, fname, **kw):
        pathlib.Path(fname).write_text(self.write_string(**kw), encoding='utf-8')
