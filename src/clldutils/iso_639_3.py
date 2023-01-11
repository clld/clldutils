"""
This module provides an API to the information of the ISO-639-3 standard.
ISO-639-3 data is not distributed with this package. Instead, an :class:`ISO` instance can either
be passed the path to a local copy of the zipped ISO tables or it will download them from
`<https://iso639-3.sil.org/code_tables/download_tables>`_
"""

import io
import re
import csv
import string
import typing
import pathlib
import datetime
import functools
import collections
import urllib.request

from clldutils.path import TemporaryDirectory
from clldutils.ziparchive import ZipArchive

__all__ = ['ISO', 'Code', 'download_tables']

BASE_URL = "https://iso639-3.sil.org/"
ZIP_NAME_PATTERN = re.compile(
    r'(?P<name>sites/iso639-3/files/downloads/iso-639-3_Code_Tables_[0-9]{8}.zip)"')
TABLE_NAME_PATTERN = re.compile(r'/iso-639-3(?P<name_and_date>[^.]*)\.tab')
DATESTAMP_PATTERN = re.compile(r'(2[0-9]{3})([0-1][0-9])([0-3][0-9])')
USER_AGENT = 'Mozilla'  # It seems a python user-agent doesn't cut it anymore.

# For some reason, the retirements code table gives the wrong replacement codes in two
# cases (although they are described correctly on the website):
CHANGE_TO_ERRATA = {
    'guv': ['duz'],
    'ymt': ['mtm'],
}


def _open(path):
    return urllib.request.urlopen(
        urllib.request.Request(BASE_URL + path, headers={'User-Agent': USER_AGENT}))


def iterrows(lines):
    header = None
    for i, row in enumerate(csv.reader(io.StringIO('\n'.join(lines)), delimiter='\t')):
        if i == 0:
            header = row
        else:
            yield collections.OrderedDict(zip(header, row))


class Table(list):

    def __init__(self, name_and_date, date, fp):
        parts = name_and_date.split('_')
        # The ISO 639-3 code tables from 2020-05-15 contain a table with a
        # malformed name - having an excess "0" in the date stamp.
        if parts[-1] == '202000515':  # pragma: no cover
            date = '20200515'
        digits = map(int, DATESTAMP_PATTERN.match(date).groups())
        self.date = datetime.date(*digits)
        name = '_'.join([p for p in parts if not DATESTAMP_PATTERN.match(p)])
        if name.startswith(('_', '-')):
            name = name[1:]
        if not name:
            name = 'Codes'
        self.name = name
        super(Table, self).__init__(list(iterrows(
            [line for line in fp.splitlines() if line.strip()],  # strip malformed lines.
        )))


def download_tables(outdir=None) -> pathlib.Path:
    """
    Download the zipped ISO tables to `outdir` or cwd.
    """
    match = ZIP_NAME_PATTERN.search(_open('code_tables/download_tables').read().decode('utf-8-sig'))
    if not match:
        raise ValueError('no matching zip file name found')  # pragma: no cover
    target = pathlib.Path(outdir or '.').joinpath(match.group('name').split('/')[-1])
    with target.open('wb') as fp:
        fp.write(_open(match.group('name')).read())
    return target


def iter_tables(zippath=None):
    with TemporaryDirectory() as tmp:
        if not zippath:
            zippath = download_tables(tmp)

        with ZipArchive(zippath) as archive:
            for name in archive.namelist():
                date = DATESTAMP_PATTERN.search(name)
                date = name[date.start():date.end()]
                match = TABLE_NAME_PATTERN.search(name)
                if match:
                    yield Table(match.group('name_and_date'), date, archive.read_text(name))


@functools.total_ordering
class Code(object):
    """
    Represents one ISO 639-3 code and its associated metadata.

    :ivar str code: The three-letter code
    :ivar str name: The language name
    """
    _code_pattern = re.compile(r'\[([a-z]{3})]')
    _scope_map = {
        'I': 'Individual',
        'M': 'Macrolanguage',
        'S': 'Special',
    }
    _type_map = {
        'L': 'Living',
        'E': 'Extinct',
        'A': 'Ancient',
        'H': 'Historical',
        'C': 'Constructed',
        'S': 'Special',
    }
    _rtype_map = {
        'C': 'change',
        'D': 'duplicate',
        'N': 'non-existent',
        'S': 'split',
        'M': 'merge',
    }

    def __init__(self, item, tablename, registry):
        code = item['Id']
        self._change_to = []
        self.retired = False
        if tablename == 'Codes':
            self._scope = self._scope_map[item['Scope']]
            self._type = self._type_map[item['Language_Type']]
        elif tablename == 'Retirements':
            self._scope = 'Retirement'
            self._type = self._rtype_map[item['Ret_Reason']] if item['Ret_Reason'] else None
            self.retired = datetime.date(*map(int, item['Effective'].split('-')))
            if code in CHANGE_TO_ERRATA:
                self._change_to = CHANGE_TO_ERRATA[code]  # pragma: no cover
            else:
                if item['Change_To']:
                    assert item['Change_To'] != code
                    self._change_to = [item['Change_To']]
                elif item['Ret_Remedy']:
                    self._change_to = [
                        c for c in self._code_pattern.findall(item['Ret_Remedy'])
                        if c != code]
        elif tablename == 'Local':
            self._scope = 'Local'
            self._type = 'Special'
        else:
            raise ValueError(tablename)  # pragma: no cover

        self.code = code
        self.name = item['Ref_Name']
        self._registry = registry

    @property
    def type(self) -> str:
        """
        The type of the code formatted as pair "scope/type"
        """
        return '{}/{}'.format(self._scope, self._type)

    @property
    def is_retired(self) -> bool:
        """
        Flag signaling whether the code is retired.
        """
        return bool(self.retired)

    @property
    def change_to(self) -> typing.List['Code']:
        """
        List of codes that supersede a retired code.
        """
        res = []
        for code in self._change_to:
            code = self._registry[code]
            if not code.is_retired:
                res.append(code)
            else:
                res.extend(code.change_to)
        return res

    @property
    def is_local(self) -> bool:
        """
        Flag signaling whether the code is in the private use area.
        """
        return self._scope == 'Local'

    @property
    def is_macrolanguage(self) -> bool:
        return self._scope == 'Macrolanguage'

    @property
    def extension(self) -> typing.List['Code']:
        """
        The codes subsumed by a macrolanguage code.
        """
        if self.is_macrolanguage:
            return [self._registry[c] for c in self._registry._macrolanguage[self.code]]
        return []

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        return self.code == other.code

    def __lt__(self, other):
        return self.code < other.code

    def __repr__(self):
        return '<ISO-639-3 [{0}] {1}>'.format(self.code, self.type)

    def __str__(self):
        return '{0} [{1}]'.format(self.name, self.code)


class ISO(collections.OrderedDict):
    """
    Provides access to the content of ISO 639-3's downloadable code table.

    An `ISO` instance maps three-letter codes to :class:`Code` instances, and provides a couple
    of convenience methods.

    Usage:

        .. code-block:: python

            >>> from clldutils.iso_639_3 import ISO
            >>> iso = ISO('iso-639-3_Code_Tables_20220311.zip')
            >>> iso.retirements[0]
            <ISO-639-3 [fri] Retirement/change>
            >>> iso.retirements[0].change_to
            [<ISO-639-3 [fry] Individual/Living>]
    """
    def __init__(self, zippath: typing.Optional[typing.Union[str, pathlib.Path]] = None):
        """
        :param zippath: Path to a local copy of the "Complete Set of Tables" (UTF-8). If `None`, \
        the tables will be retrieved from the web.
        """
        zippath = pathlib.Path(zippath) if zippath else None
        self._tables = {t.name: t for t in iter_tables(zippath=zippath)}
        if zippath and DATESTAMP_PATTERN.search(zippath.name):
            digits = map(int, DATESTAMP_PATTERN.search(zippath.name).groups())
            self.date = datetime.date(*digits)
        else:
            self.date = max(t.date for t in self._tables.values())
        self._macrolanguage = collections.defaultdict(list)
        for item in self._tables['macrolanguages']:
            self._macrolanguage[item['M_Id']].append(item['I_Id'])
        super(ISO, self).__init__()
        for tablename in ['Codes', 'Retirements']:
            for item in self._tables[tablename]:
                if item['Id'] not in self:
                    # Note: we don't keep historical retirements, i.e. ones that have only
                    # been in effect for some time. E.g. lcq has been changed to ppr
                    # from 2012-02-03 until 2013-01-23 when it was changed back to lcq
                    self[item['Id']] = Code(item, tablename, self)
        for code in ['q' + x + y
                     for x in string.ascii_lowercase[:string.ascii_lowercase.index('t') + 1]
                     for y in string.ascii_lowercase]:
            self[code] = Code(dict(Id=code, Ref_Name=None), 'Local', self)

    def __str__(self):
        return 'ISO 639-3 code tables from {0}'.format(self.date)

    def by_type(self, type_) -> typing.List[Code]:
        return [c for c in self.values() if c._type == type_]

    @property
    def living(self) -> typing.List[Code]:
        """
        All codes categorized as "Living"
        """
        return self.by_type('Living')

    @property
    def extinct(self) -> typing.List[Code]:
        """
        All codes categorized as "Extinct"
        """
        return self.by_type('Extinct')

    @property
    def ancient(self) -> typing.List[Code]:
        """
        All codes categorized as "Ancient"
        """
        return self.by_type('Ancient')

    @property
    def historical(self) -> typing.List[Code]:
        """
        All codes categorized as "Historical"
        """
        return self.by_type('Historical')

    @property
    def constructed(self) -> typing.List[Code]:
        """
        All codes categorized as "Constructed"
        """
        return self.by_type('Constructed')

    @property
    def special(self) -> typing.List[Code]:
        """
        All codes categorized as "Special"
        """
        return self.by_type('Special')

    @property
    def retirements(self) -> typing.List[Code]:
        """
        All retired codes
        """
        return [c for c in self.values() if c.is_retired]

    @property
    def macrolanguages(self) -> typing.List[Code]:
        """
        All macrolanguage codes
        """
        return [c for c in self.values() if c.is_macrolanguage]

    @property
    def languages(self) -> typing.List[Code]:
        """
        All active language codes
        """
        return [c for c in self.values()
                if not c.is_macrolanguage and not c.is_retired and not c.is_local]
