import argparse

import attr
import pytest

from clldutils.apilib import API, DataObject, latitude, longitude, VERSION_NUMBER_PATTERN


def test_API():
    api = API('.')
    assert api.repos.exists()
    assert 'repository' in '%s' % api
    assert not api.path('unknown', 'path').exists()


def test_API_custom_md():
    class C(API):
        __default_metadata__ = {'title': 'x'}
    api = C('.')
    assert api.dataset_metadata.title == 'x'


def test_API_assert_release(tmp_path):
    api = API(tmp_path)
    with pytest.raises(AssertionError):
        api.assert_release()


def test_API_with_app(tmp_path, mocker):
    wb = mocker.Mock()
    mocker.patch('clldutils.apilib.webbrowser', wb)
    tmp_path.joinpath('app').mkdir()

    @API.app_wrapper
    def f(args):
        tmp_path.joinpath('app', 'index.html').write_text('<html/>', encoding='utf8')
        wb.create()

    f(argparse.Namespace(repos=str(tmp_path)))
    assert tmp_path.joinpath('app', 'data').exists()
    assert wb.create.call_count == 1
    assert wb.open.called
    f(argparse.Namespace(repos=str(tmp_path)))
    assert wb.create.call_count == 1
    f(argparse.Namespace(repos=API(str(tmp_path)), args=['--recreate']))
    assert wb.create.call_count == 2
    f(argparse.Namespace(repos=API(str(tmp_path)), recreate=True))
    assert wb.create.call_count == 3


def test_DataObject():
    @attr.s
    class C(DataObject):
        x = attr.ib()
        y = attr.ib(metadata=dict(ascsv=lambda v: 'xyz'))

    assert C.fieldnames() == ['x', 'y']
    assert C(None, 2).ascsv() == ['', 'xyz']
    assert C(['y', 'x'], 2).ascsv() == ['y;x', 'xyz']
    assert C({'y': 2}, 2).ascsv() == ['{"y": 2}', 'xyz']
    assert C(2.123456, 'x').ascsv() == ['2.12346', 'xyz']
    assert C(2, 'x').ascsv() == ['2', 'xyz']


def test_latitude_longitude():
    @attr.s
    class C(object):
        lat = latitude()
        lon = longitude()

    assert C('', None).lat is None

    with pytest.raises(ValueError):
        C(lat=100, lon=50)

    with pytest.raises(ValueError):
        C(lat='10', lon='500')


def test_VERSION_NUMBER_PATTERN():
    assert VERSION_NUMBER_PATTERN.match('v1.2').group('number') == '1.2'
    assert not VERSION_NUMBER_PATTERN.match('1.2')
    assert not VERSION_NUMBER_PATTERN.match('v1.2.a2')
