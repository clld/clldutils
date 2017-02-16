# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase


class Tests(TestCase):
    def test_replace(self):
        from clldutils.lgr import replace

        for i, o in [
            ('1SG', '<first person singular>'),
            ('DUR.DU-', '<durative>.<dual>-'),
        ]:
            self.assertEqual(replace(i), o)

        self.assertEqual(replace('DUR.DU-', lambda m: m.group('pre') + '#'), '#.#-')
        self.assertEqual(replace('.XX-', custom={'XX': 'x'}), '.<x>-')
