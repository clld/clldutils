"""
Functionality to handle SIL Standard Format (SFM) files

Supports
- multiline values
- custom entry separater
"""
from __future__ import unicode_literals
import re
from collections import Counter
import io

from clldutils.misc import UnicodeMixin
from clldutils.path import Path, as_posix


MARKER_PATTERN = re.compile('\\\\(?P<marker>[A-Za-z1-3][A-Za-z_]*)(\s+|$)')
FIELD_SPLITTER_PATTERN = re.compile(';\s+')


def marker_split(block):
    """generate marker, value pairs from a text block (i.e. a list of lines).
    """
    marker = None
    value = []

    for line in block.split('\n'):
        line = line.strip()
        if line.startswith('\\_'):
            continue  # we simply ignore SFM header fields
        match = MARKER_PATTERN.match(line)
        if match:
            if marker:
                yield marker, '\n'.join(value)
            marker = match.group('marker')
            value = [line[match.end():]]
        else:
            value.append(line)
    if marker:
        yield marker, ('\n'.join(value)).strip()


class Entry(list, UnicodeMixin):
    """We store entries in SFM files as lists of (marker, value) pairs.
    """
    @classmethod
    def from_string(cls, block):
        entry = cls()
        for marker, value in marker_split(block.strip()):
            value = value.strip()
            if value:
                entry.append((marker, value))
        return entry

    def markers(self):
        return Counter([k for k, v in self])

    def get(self, key, default=None):
        """Use get to retrieve the first value for a marker or None.
        """
        for k, v in self:
            if k == key:
                return v
        return default

    def getall(self, key):
        """Use getall to retrieve all values for a marker.
        """
        return [v for k, v in self if k == key]

    def __unicode__(self):
        lines = []
        for key, value in self:
            lines.append('%s %s' % (key, value))
        return '\n'.join('\\' + l for l in lines)


def read(filename, encoding):
    # we cannot use codecs.open, because it does not understand mode U.
    if isinstance(filename, Path):
        filename = as_posix(filename)
    with open(filename, 'rU') as fp:
        return fp.read().decode(encoding)


def parse(filename, encoding, entry_impl, entry_sep, entry_prefix, marker_map):
    for block in read(filename, encoding).split(entry_sep):
        if block.strip():
            block = entry_prefix + block
        else:
            continue  # pragma: no cover
        rec = entry_impl()
        for marker, value in marker_split(block.strip()):
            value = value.strip()
            if value:
                rec.append((marker_map.get(marker, marker), value))
        if rec:
            yield rec


class SFM(list):
    """
    A list of Entries

    Simple usage to normalize a sfm file:

    >>> sfm = SFM()
    >>> sfm.read(fname, marker_map={'lexeme': 'lx'})
    >>> sfm.write(fname)
    """
    def read(self,
             filename,
             encoding='utf8',
             marker_map=None,
             entry_impl=Entry,
             entry_sep='\n\n',
             entry_prefix=None):
        """
        Extend the list by parsing new entries from a file.

        :param filename:
        :param encoding:
        :param marker_map: A dict used to map marker names.
        :param entry_impl:
        :param entry_sep:
        :param entry_prefix:
        :return:
        """
        for entry in parse(
                filename,
                encoding,
                entry_impl,
                entry_sep,
                entry_prefix or entry_sep,
                marker_map or {}):
            self.append(entry)

    def visit(self, visitor):
        for i, entry in enumerate(self):
            self[i] = visitor(entry) or entry

    def write(self, filename, encoding='utf8'):
        """
        Write the list of entries to a file.

        :param filename:
        :param encoding:
        :return:
        """
        if isinstance(filename, Path):
            filename = as_posix(filename)
        with io.open(filename, 'w', encoding=encoding) as fp:
            for entry in self:
                fp.write(entry.__unicode__())
                fp.write('\n\n')
