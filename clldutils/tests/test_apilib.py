# coding: utf8
from __future__ import unicode_literals, print_function, division
from functools import partial
from unittest import TestCase
import re

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

    def test_valid_re(self):
        from clldutils.apilib import valid_re

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_re, '(a[0-9]+)?$'))

        self.assertEqual(C('a1').a, 'a1')
        self.assertEqual(C('').a, '')

        with self.assertRaises(ValueError):
            C('b')

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_re, re.compile('a[0-9]+'), nullable=True))

        self.assertEqual(C(None).a, None)

        with self.assertRaises(ValueError):
            C('b')

    def test_valid_range(self):
        from clldutils.apilib import valid_range

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_range, -1, 5))

        self.assertEqual(C(0).a, 0)
        with self.assertRaises(ValueError):
            C(-3)

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_range, 0, None))

        self.assertEqual(C(2).a, 2)
        with self.assertRaises(ValueError):
            C(-1)

    def test_valid_enum_member(self):
        from clldutils.apilib import valid_enum_member

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_enum_member, [1, 2, 3]))

        self.assertEqual(C(3).a, 3)

        with self.assertRaises(ValueError):
            C(5)
