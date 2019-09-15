"""Programmatic access to the information of the ISO-639-3 standard

ISO-639-3 data is not distributed with this package, but we fetch the download listed at
http://www-01.sil.org/iso639-3/download.asp
"""

import re
import functools
import datetime
from collections import defaultdict, OrderedDict
from string import ascii_lowercase
from urllib.request import urlopen, Request

from csvw.dsv import iterrows

from clldutils.path import TemporaryDirectory, Path
from clldutils.ziparchive import ZipArchive

BASE_URL = "https://iso639-3.sil.org/"
ZIP_NAME_PATTERN = re.compile(
    '(?P<name>sites/iso639-3/files/downloads/iso-639-3_Code_Tables_[0-9]{8}.zip)"')
TABLE_NAME_PATTERN = re.compile('/iso-639-3(?P<name_and_date>[^.]+)\.tab')
DATESTAMP_PATTERN = re.compile('(2[0-9]{3})([0-1][0-9])([0-3][0-9])')
USER_AGENT = 'Mozilla'  # It seems a python user-agent doesn't cut it anymore.

# For some reason, the retirements code table gives the wrong replacement codes in two
# cases (although they are described correctly on the website):
CHANGE_TO_ERRATA = {
    'guv': ['duz'],
    'ymt': ['mtm'],
}


def _open(path):
    return urlopen(Request(BASE_URL + path, headers={'User-Agent': USER_AGENT}))


class Table(list):

    def __init__(self, name_and_date, fp):
        parts = name_and_date.split('_')
        digits = map(int, DATESTAMP_PATTERN.match(parts[-1]).groups())
        self.date = datetime.date(*digits)
        name = '_'.join(parts[:-1])
        if name.startswith(('_', '-')):
            name = name[1:]
        if not name:
            name = 'Codes'
        self.name = name
        super(Table, self).__init__(iterrows(
            [line for line in fp.splitlines() if line.strip()],  # strip malformed lines.
            dicts=True,
            delimiter='\t'))


def download_tables(outdir=None):
    match = ZIP_NAME_PATTERN.search(_open('code_tables/download_tables').read().decode('utf-8-sig'))
    if not match:
        raise ValueError('no matching zip file name found')  # pragma: no cover
    target = Path(outdir or '.').joinpath(match.group('name').split('/')[-1])
    with target.open('wb') as fp:
        fp.write(_open(match.group('name')).read())
    return target


def iter_tables(zippath=None):
    with TemporaryDirectory() as tmp:
        if not zippath:
            zippath = download_tables(tmp)

        with ZipArchive(zippath) as archive:
            for name in archive.namelist():
                match = TABLE_NAME_PATTERN.search(name)
                if match:
                    yield Table(match.group('name_and_date'), archive.read_text(name))


@functools.total_ordering
class Code(object):

    _code_pattern = re.compile('\[([a-z]{3})\]')
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
            self._type = self._rtype_map[item['Ret_Reason']]
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
    def type(self):
        return '{0}/{1}'.format(self._scope, self._type)

    @property
    def is_retired(self):
        return bool(self.retired)

    @property
    def change_to(self):
        res = []
        for code in self._change_to:
            code = self._registry[code]
            if not code.is_retired:
                res.append(code)
            else:
                res.extend(code.change_to)
        return res

    @property
    def is_local(self):
        return self._scope == 'Local'

    @property
    def is_macrolanguage(self):
        return self._scope == 'Macrolanguage'

    @property
    def extension(self):
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


class ISO(OrderedDict):

    def __init__(self, zippath=None):
        self._tables = {t.name: t for t in iter_tables(zippath=zippath)}
        if zippath and DATESTAMP_PATTERN.search(zippath.name):
            digits = map(int, DATESTAMP_PATTERN.search(zippath.name).groups())
            self.date = datetime.date(*digits)
        else:
            self.date = max(t.date for t in self._tables.values())
        self._macrolanguage = defaultdict(list)
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
                     for x in ascii_lowercase[:ascii_lowercase.index('t') + 1]
                     for y in ascii_lowercase]:
            self[code] = Code(dict(Id=code, Ref_Name=None), 'Local', self)

    def __str__(self):
        return 'ISO 639-3 code tables from {0}'.format(self.date)

    def by_type(self, type_):
        return [c for c in self.values() if c._type == type_]

    @property
    def living(self):
        return self.by_type('Living')

    @property
    def extinct(self):
        return self.by_type('Extinct')

    @property
    def ancient(self):
        return self.by_type('Ancient')

    @property
    def historical(self):
        return self.by_type('Historical')

    @property
    def constructed(self):
        return self.by_type('Constructed')

    @property
    def special(self):
        return self.by_type('Special')

    @property
    def retirements(self):
        return [c for c in self.values() if c.is_retired]

    @property
    def macrolanguages(self):
        return [c for c in self.values() if c.is_macrolanguage]

    @property
    def languages(self):
        return [c for c in self.values()
                if not c.is_macrolanguage and not c.is_retired and not c.is_local]
