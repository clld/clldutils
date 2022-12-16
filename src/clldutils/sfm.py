"""
SIL's Standard Format (SFM) files are used natively for Toolbox. Applications which can export in
a SFM format include ELAN and Flex. In absence of other export formats, the need to read or write
SFM files persists.

The (somewhat simplistic) SFM implementation provided in this module supports

- multiline values
- custom entry separator

Usage:

.. code-block:: python

    >>> from clldutils.sfm import SFM
    >>> sfm = SFM.from_string('''\\ex Yax bo’on ta sna Antonio.
    ... \\exEn I’m going to Antonio’s house.
    ... \\ex Ban yax ba’at?
    ... \\exEn Where are you going?
    ... \\exFr Ou allez-vous?''')
    >>> sfm[0].markers()
    Counter({'ex': 2, 'exEn': 2, 'exFr': 1})
    >>> sfm[0].get('exFr')
    'Ou allez-vous?'
"""

import re
import typing
import pathlib
import collections

__all__ = ['Entry', 'SFM']

MARKER_PATTERN = re.compile(r'\\(?P<marker>[A-Za-z0-9][A-Za-z0-9_]*)(\s+|$)')

FIELD_SPLITTER_PATTERN = re.compile(r';\s+')


def marker_split(block: str) -> typing.Generator[typing.Tuple[str, str], None, None]:
    """
    Yield marker, value pairs from a text block (i.e. a list of lines).

    :param block: text block consisting of newline separated lines as it will be the case for \
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


class Entry(list):
    """We store entries in SFM files as lists of (marker, value) pairs."""

    @classmethod
    def from_string(cls, block, keep_empty=False):
        entry = cls()
        for marker, value in marker_split(block.strip()):
            value = value.strip()
            if value or keep_empty:
                entry.append((marker, value))
        return entry

    def markers(self) -> collections.Counter:
        """
        Map of markers to frequency counts.
        """
        return collections.Counter(k for k, _ in self)

    def get(self, key, default=None) -> str:
        """Retrieve the first value for a marker or None."""
        for k, v in self:
            if k == key:
                return v
        return default

    def getall(self, key) -> typing.List[str]:
        """Retrieve all values for a marker."""
        return [v for k, v in self if k == key]

    def __str__(self):
        lines = []
        for key, value in self:
            lines.append('%s %s' % (key, value))
        return '\n'.join('\\' + line for line in lines)


def parse(content,
          encoding: str = 'utf-8',
          entry_sep: str = '\n\n',
          entry_prefix: typing.Optional[str] = None,
          keep_empty=False):
    entry_prefix = entry_prefix or entry_sep

    if isinstance(content, pathlib.Path):
        with pathlib.Path(content).open('r', encoding=encoding, newline=None) as fp:
            content = fp.read()

    assert isinstance(content, str)
    for block in content.split(entry_sep):
        if block.strip():
            block = entry_prefix + block
        else:
            continue  # pragma: no cover
        yield [(k, v.strip())
               for k, v in marker_split(block.strip()) if v.strip() or keep_empty]


class SFM(list):
    """A list of Entries

    Simple usage to normalize a sfm file:

    .. code-block:: python

        >>> sfm = SFM.from_file(fname, marker_map={'lexeme': 'lx'})
        >>> sfm.write(fname)
    """

    @classmethod
    def from_file(cls, filename, **kw):
        """
        Initialize a `SFM` object from the contents of a file.
        """
        sfm = cls()
        sfm.read(filename, **kw)
        return sfm

    @classmethod
    def from_string(cls,
                    text: str,
                    marker_map: typing.Optional[typing.Dict[str, str]] = None,
                    entry_impl=Entry,
                    **kw):
        """
        Initialize a `SFM` object from a SFM formatted string.
        """
        sfm = cls()
        marker_map = marker_map or {}
        for entry in parse(text, **kw):
            if entry:
                sfm.append(entry_impl([(marker_map.get(k, k), v) for k, v in entry]))
        return sfm

    def read(self,
             filename,
             encoding='utf-8',
             marker_map: typing.Optional[typing.Dict[str, str]] = None,
             entry_impl=Entry,
             entry_sep: str = '\n\n',
             entry_prefix: typing.Optional[str] = None,
             keep_empty: bool = False):
        """Extend the entry list by parsing new entries from a file.

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

    def visit(self, visitor: typing.Callable):
        """
        Run `visitor` on each entry.
        """
        for i, entry in enumerate(self):
            self[i] = visitor(entry) or entry

    def write(self, filename, encoding='utf-8'):
        """Write the list of entries to a file.

        :param filename:
        :param encoding:
        """
        with pathlib.Path(filename).open('w', encoding=encoding) as fp:
            for entry in self:
                fp.write(str(entry))
                fp.write('\n\n')
