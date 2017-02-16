# coding: utf8
from __future__ import unicode_literals

import clldutils
from clldutils.path import Path
from clldutils.testing import WithTempDir


FIXTURES = Path(clldutils.__file__).parent.joinpath('tests', 'fixtures')


class Tests(WithTempDir):
    def test_Dictionary(self):
        from clldutils.sfm import SFM

        d = SFM.from_file(FIXTURES.joinpath('test.sfm'), keep_empty=True)
        self.assertIsNotNone(d[1].get('empty'))

        d = SFM.from_file(FIXTURES.joinpath('test.sfm'))
        self.assertEquals(len(d), 2)
        self.assertIsNone(d[1].get('empty'))
        tmp = self.tmp_path('test')
        d.write(tmp)
        d2 = SFM()
        d2.read(tmp)
        self.assertEquals(d[0].get('marker'), d2[0].get('marker'))
        self.assertEquals(d[1].get('marker'), d2[1].get('marker'))

        self.assertEquals(d[0].get('key'), None)
        d.visit(lambda e: e.append(('key', 'value')))
        self.assertEquals(d[0].get('key'), 'value')

    def test_Entry(self):
        from clldutils.sfm import Entry

        e = Entry.from_string('\\lx1 lexeme\n\\marker äöü\nabc\n\\marker next val')
        self.assertEquals(e.get('lx1'), 'lexeme')
        self.assertEquals(e.get('marker'), 'äöü\nabc')
        self.assertEquals(e.getall('marker')[1], 'next val')
        self.assertEquals(e.markers()['marker'], 2)
        self.assertEquals(e.get('x', 5), 5)

        e = Entry.from_string('\\empty\n')
        self.assertIsNone(e.get('empty'))

        e = Entry.from_string('\\empty\n', keep_empty=True)
        self.assertIsNotNone(e.get('empty'))
