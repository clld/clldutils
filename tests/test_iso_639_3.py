import io
from shutil import copy
from pathlib import Path

from clldutils.iso_639_3 import ISO, Code

FIXTURES = Path(__file__).parent.joinpath('fixtures')


def test_ISO_download(mocker):
    def urlopen(req):
        if req.get_full_url().endswith('.zip'):
            return FIXTURES.joinpath('iso.zip').open('rb')
        return io.BytesIO(
            b' href="sites/iso639-3/files/downloads/iso-639-3_Code_Tables_12345678.zip" ')

    mocker.patch('clldutils.iso_639_3.urllib.request.urlopen', urlopen)
    iso = ISO()
    assert 'aab' in iso


def test_ISO(tmp_path):
    dated_zip = tmp_path / '20121201.zip'
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


def test_zips(fixtures_dir):
    ISO(fixtures_dir / 'iso-639-3_Code_Tables_20210218.zip')
