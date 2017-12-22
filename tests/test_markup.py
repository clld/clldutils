# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
from operator import itemgetter


class Tests(TestCase):
    def test_Table(self):
        from clldutils.markup import Table

        t = Table()
        self.assertEqual(t.render(), '')

        t = Table('a', 'b', rows=[[1, 2], [3, 4]])
        self.assertEqual(
            t.render(),
            '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |')
        self.assertEqual(
            t.render(condensed=False),
            '|   a |   b |\n|----:|----:|\n|   1 |   2 |\n|   3 |   4 |')
        self.assertEqual(
            t.render(verbose=True),
            '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |\n\n(2 rows)\n\n')
        self.assertEqual(
            t.render(sortkey=itemgetter(1), reverse=True),
            '| a | b |\n|----:|----:|\n| 3 | 4 |\n| 1 | 2 |')
