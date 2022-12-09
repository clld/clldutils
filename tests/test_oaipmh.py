import io
import datetime
import contextlib

from clldutils.oaipmh import *


def test_iter_records(fixtures_dir, mocker):
    class UrllibRequest:
        @contextlib.contextmanager
        def urlopen(self, *args):
            yield io.BytesIO(fixtures_dir.joinpath('oaipmh.xml').read_bytes())

    mocker.patch('clldutils.oaipmh.urllib.request', UrllibRequest())

    i = -1
    for i, rec in enumerate(iter_records(
            'http://example.org',
            set_='spec',
            from_='2022-10-10',
            until=datetime.date.today())):
        if i == 0:
            assert 'user-cldf-datasets' in rec.sets
            assert rec.oai_dc_metadata['creator'] == ['Eline Visser']
        if i > 150:
            break
    assert i == 151


def test_iter_records_no_rt(fixtures_dir, mocker):
    class UrllibRequest:
        @contextlib.contextmanager
        def urlopen(self, *args):
            yield io.BytesIO(fixtures_dir.joinpath('oaipmh_no_rt.xml').read_bytes())

    mocker.patch('clldutils.oaipmh.urllib.request', UrllibRequest())

    assert len(list(iter_records('http://example.org'))) == 100
