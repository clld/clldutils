# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase

import attr


class Tests(TestCase):
    def test_API(self):
        from clldutils.apilib import API

        api = API('.')
        assert api.repos.exists()
        self.assertIn('repository', '%s' % api)

        assert not api.path('unknown', 'path').exists()

    def test_DataObject(self):
        from clldutils.apilib import DataObject

        @attr.s
        class C(DataObject):
            x = attr.ib()
            y = attr.ib(metadata=dict(ascsv=lambda v: 'xyz'))

        self.assertEqual(C.fieldnames(), ['x', 'y'])
        self.assertEqual(C(None, 2).ascsv(), ['', 'xyz'])
        self.assertEqual(C(['y', 'x'], 2).ascsv(), ['y;x', 'xyz'])
        self.assertEqual(C({'y': 2}, 2).ascsv(), ['{"y": 2}', 'xyz'])
        self.assertEqual(C(2.123456, 'x').ascsv(), ['2.12346', 'xyz'])
        self.assertEqual(C(2, 'x').ascsv(), ['2', 'xyz'])

    def test_latitude_longitude(self):
        from clldutils.apilib import latitude, longitude

        @attr.s
        class C(object):
            lat = latitude()
            lon = longitude()

        self.assertIsNone(C('', None).lat)

        with self.assertRaises(ValueError):
            C(lat=100, lon=50)

        with self.assertRaises(ValueError):
            C(lat='10', lon='500')
