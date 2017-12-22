# coding: utf8
from __future__ import unicode_literals

from clldutils.path import Path
from clldutils.sfm import SFM, Entry


def test_Dictionary(tmppath):
    p = Path(__file__).parent.joinpath('fixtures', 'test.sfm')
    d = SFM.from_file(p, keep_empty=True)
    assert d[1].get('empty') is not None

    d = SFM.from_file(p)
    assert len(d) == 2
    assert d[1].get('empty') is None
    tmp = tmppath / 'test'
    d.write(tmp)
    d2 = SFM()
    d2.read(tmp)
    assert d[0].get('marker') == d2[0].get('marker')
    assert d[1].get('marker') == d2[1].get('marker')

    assert d[0].get('key') is None
    d.visit(lambda e: e.append(('key', 'value')))
    assert d[0].get('key') == 'value'


def test_Entry():
    e = Entry.from_string('\\lx1 lexeme\n\\marker äöü\nabc\n\\marker next val')
    assert e.get('lx1') == 'lexeme'
    assert e.get('marker') == 'äöü\nabc'
    assert e.getall('marker')[1] == 'next val'
    assert e.markers()['marker'] == 2
    assert e.get('x', 5) == 5

    e = Entry.from_string('\\empty\n')
    assert e.get('empty') is None

    e = Entry.from_string('\\empty\n', keep_empty=True)
    assert e.get('empty') is not None
