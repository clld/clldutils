from pathlib import Path

from clldutils.sfm import *


def test_from_string():
    sfm = SFM.from_string(r'''\ex Yax bo’on ta sna Antonio.
\exEn I’m going to Antonio’s house.
\ex Ban yax ba’at?
\exEn Where are you going?
\exFr Ou allez-vous?''')
    assert sfm[0].markers()['ex'] == 2
    assert sfm[0].get('exFr') == 'Ou allez-vous?'


def test_Dictionary(tmp_path):
    p = Path(__file__).parent.joinpath('fixtures', 'test.sfm')
    d = SFM.from_file(p, keep_empty=True)
    assert d[1].get('empty') is not None

    d = SFM.from_file(p)
    assert len(d) == 2
    assert d[1].get('empty') is None
    tmp = tmp_path / 'test'
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


def test_Entry_with_numeric_marker():
    e = Entry.from_string('\\z10_Eng abc')
    assert e.get('z10_Eng') == 'abc'

