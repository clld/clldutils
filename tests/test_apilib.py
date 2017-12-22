# coding: utf8
from __future__ import unicode_literals, print_function, division

import attr
import pytest

from clldutils.apilib import API, DataObject, latitude, longitude


def test_API():
    api = API('.')
    assert api.repos.exists()
    assert 'repository' in '%s' % api
    assert not api.path('unknown', 'path').exists()


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
