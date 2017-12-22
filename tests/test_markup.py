# coding: utf8
from __future__ import unicode_literals, print_function, division
from operator import itemgetter


def test_Table():
    from clldutils.markup import Table

    t = Table()
    assert t.render() == ''

    t = Table('a', 'b', rows=[[1, 2], [3, 4]])
    assert t.render() == \
        '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |'
    assert t.render(condensed=False) == \
        '|   a |   b |\n|----:|----:|\n|   1 |   2 |\n|   3 |   4 |'
    assert t.render(verbose=True) == \
        '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |\n\n(2 rows)\n\n'
    assert t.render(sortkey=itemgetter(1), reverse=True) == \
        '| a | b |\n|----:|----:|\n| 3 | 4 |\n| 1 | 2 |'
