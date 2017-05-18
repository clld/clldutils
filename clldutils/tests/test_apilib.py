# coding: utf8
from __future__ import unicode_literals, print_function, division
from functools import partial
from unittest import TestCase

import attr


class Tests(TestCase):
    def test_API(self):
        from clldutils.apilib import API

        api = API('.')
        assert api.repos.exists()
        self.assertIn('repository', '%s' % api)

        assert not api.path('unknown', 'path').exists()

    def test_valid_range(self):
        from clldutils.apilib import valid_range

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_range, -1, 5))

        self.assertEqual(C(0).a, 0)

        with self.assertRaises(ValueError):
            C(-3)

    def test_valid_enum_member(self):
        from clldutils.apilib import valid_enum_member

        @attr.s
        class C(object):
            a = attr.ib(validator=partial(valid_enum_member, [1, 2, 3]))

        self.assertEqual(C(3).a, 3)

        with self.assertRaises(ValueError):
            C(5)
