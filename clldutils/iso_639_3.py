# coding: utf8
"""
Programmatic access to the information of the ISO-639-3 standard

ISO-639-3 data is not distributed with this package, but we fetch the download listed at
http://www-01.sil.org/iso639-3/download.asp
"""
from __future__ import unicode_literals, print_function, division
import re
from datetime import date
from collections import defaultdict

from six.moves.urllib.request import urlretrieve, urlopen

from clldutils.path import TemporaryDirectory
from clldutils.ziparchive import ZipArchive
from clldutils.dsv import reader

BASE_URL = "http://www-01.sil.org/iso639-3/"
ZIP_NAME_PATTERN = re.compile('href="(?P<name>iso-639-3_Code_Tables_[0-9]{8}.zip)"')
TABLE_NAME_PATTERN = re.compile('/iso-639-3(?P<name_and_date>[^\.]+)\.tab')


class Table(list):
    def __init__(self, name_and_date, fp):
        parts = name_and_date.split('_')
        self.date = date(int(parts[-1][:4]), int(parts[-1][4:6]), int(parts[-1][6:8]))
        name = '_'.join(parts[:-1])
        if name.startswith('_') or name.startswith('-'):
            name = name[1:]
        if not name:
            name = 'Codes'
        self.name = name
        list.__init__(self, reader(fp.splitlines(), namedtuples=True, delimiter='\t'))


def iter_tables():
    zipname = None
    match = ZIP_NAME_PATTERN.search(urlopen(BASE_URL + 'download.asp').read())
    if match:
        zipname = match.group('name')

    if not zipname:
        raise ValueError('no matching zip file name found')  # pragma: no cover

    with TemporaryDirectory() as tmp:
        zippath = tmp.joinpath('tables.zip')
        urlretrieve(BASE_URL + zipname, zippath.as_posix())
        with ZipArchive(zippath) as archive:
            for name in archive.namelist():
                match = TABLE_NAME_PATTERN.search(name)
                if match:
                    yield Table(match.group('name_and_date'), archive.read_text(name))


class ISO(object):
    def __init__(self):
        self.tables = {t.name: t for t in iter_tables()}
        self.macrolanguage = defaultdict(list)
        for item in self.tables['macrolanguages']:
            self.macrolanguage[item.M_Id].append(item.I_Id)
        self.retired = {i.Id: i for i in self.tables['Retirements']}
        self.active = {i.Id: i for i in self.tables['Codes']}

    def __contains__(self, item):
        return item in self.macrolanguage or item in self.retired or item in self.active
