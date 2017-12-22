# coding: utf8
from __future__ import unicode_literals, print_function, division

from clldutils.path import copy, Path

FIXTURES = Path(__file__).parent.joinpath('fixtures')


def test_ISO_download(mocker):
    from clldutils.iso_639_3 import ISO

    def urlopen(*args, **kw):
        return mocker.Mock(read=mocker.Mock(
            return_value=' href="iso-639-3_Code_Tables_12345678.zip" '))

    def urlretrieve(url, dest):
        copy(FIXTURES.joinpath('iso.zip'), dest)

    mocker.patch.multiple('clldutils.iso_639_3', urlopen=urlopen, urlretrieve=urlretrieve)
    iso = ISO()
    assert 'aab' in iso


def test_ISO(tmppath):
    from clldutils.iso_639_3 import ISO, Code

    dated_zip = tmppath / '20121201.zip'
    copy(FIXTURES.joinpath('iso.zip'), dated_zip)
    iso = ISO(dated_zip)
    assert '{0}'.format(iso) == 'ISO 639-3 code tables from 2012-12-01'

    iso = ISO(FIXTURES.joinpath('iso.zip'))
    assert '{0}'.format(iso) == 'ISO 639-3 code tables from 2016-07-25'
    for attr in Code._type_map.values():
        assert isinstance(getattr(iso, attr.lower()), list)

    assert len(iso.languages) == 7
    assert len(iso.macrolanguages[0].extension) == 2
    assert len(iso.languages[0].extension) == 0
    assert len(iso.retirements[0].change_to) == 1
    assert iso['auv'].change_to[0] in iso.languages
    d = {iso['auv']: 1}
    assert iso['auv'] in d
    assert '[twi]' in repr(sorted(iso.values(), reverse=True)[0])
    assert '%s' % iso['aab'] == 'Alumu-Tesu [aab]'
