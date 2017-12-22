# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase


class Tests(TestCase):
    def test_find(self):
        from clldutils.licenses import find

        self.assertEqual(
            find('http://creativecommons.org/licenses/by/4.0').id, 'CC-BY-4.0')
        self.assertEqual(
            find('CC-BY-4.0').url, 'https://creativecommons.org/licenses/by/4.0/')
