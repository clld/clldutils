"""
Functionality to handle SIL Standard Format (SFM) files

#
# FIXME: seealso link for SFM spec!
#

This format is used natively for Toolbox. Applications which can export in a SFM format
include
- ELAN   FIXME: link!
- Flex   FIXME: link!

This implementation supports
- multiline values
- custom entry separator
"""
from __future__ import unicode_literals
import re
from collections import Counter
from io import open

from clldutils.misc import UnicodeMixin
from clldutils.path import Path, as_posix


MARKER_PATTERN = re.compile('\\\\(?P<marker>[A-Za-z1-3][A-Za-z_]*[0-9]*)(\s+|$)')
FIELD_SPLITTER_PATTERN = re.compile(';\s+')


def marker_split(block):
    """
    generate marker, value pairs from a text block (i.e. a list of lines).

    :param block: text block consisting of \n separated lines as it will be the case for \
    files read using "rU" mode.
    :return: generator of (marker, value) pairs.
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
    def from_string(cls, block, keep_empty=False):
        entry = cls()
        for marker, value in marker_split(block.strip()):
            value = value.strip()
            if value or keep_empty:
                entry.append((marker, value))
        return entry

    def markers(self):
        return Counter([k for k, v in self])

    def get(self, key, default=None):
        """Retrieve the first value for a marker or None."""
        for k, v in self:
            if k == key:
                return v
        return default

    def getall(self, key):
        """Retrieve all values for a marker."""
        return [v for k, v in self if k == key]

    def __unicode__(self):
        lines = []
        for key, value in self:
            lines.append('%s %s' % (key, value))
        return '\n'.join('\\' + l for l in lines)


def parse(filename, encoding, entry_sep, entry_prefix, keep_empty=False):
    if isinstance(filename, Path):
        filename = as_posix(filename)

    # we cannot use codecs.open, because it does not understand mode U.
    with open(filename, 'rU', encoding=encoding) as fp:
        content = fp.read()

    for block in content.split(entry_sep):
        if block.strip():
            block = entry_prefix + block
        else:
            continue  # pragma: no cover
        yield [(k, v.strip())
               for k, v in marker_split(block.strip()) if v.strip() or keep_empty]


class SFM(list):
    """
    A list of Entries

    Simple usage to normalize a sfm file:

    >>> sfm = SFM.from_file(fname, marker_map={'lexeme': 'lx'})
    >>> sfm.write(fname)
    """
    @classmethod
    def from_file(cls, filename, **kw):
        sfm = cls()
        sfm.read(filename, **kw)
        return sfm

    def read(self,
             filename,
             encoding='utf8',
             marker_map=None,
             entry_impl=Entry,
             entry_sep='\n\n',
             entry_prefix=None,
             keep_empty=False):
        """
        Extend the list by parsing new entries from a file.

        :param filename:
        :param encoding:
        :param marker_map: A dict used to map marker names.
        :param entry_impl: Subclass of Entry or None
        :param entry_sep:
        :param entry_prefix:
        """
        marker_map = marker_map or {}
        for entry in parse(
                filename,
                encoding,
                entry_sep,
                entry_prefix or entry_sep,
                keep_empty=keep_empty):
            if entry:
                self.append(entry_impl([(marker_map.get(k, k), v) for k, v in entry]))

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
        with open(filename, 'w', encoding=encoding) as fp:
            for entry in self:
                fp.write(entry.__unicode__())
                fp.write('\n\n')
