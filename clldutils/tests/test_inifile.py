# coding: utf8
from __future__ import unicode_literals, print_function

from clldutils.testing import WithTempDir


class Tests(WithTempDir):
    def test_INI(self):
        from clldutils.inifile import INI

        ini = INI()
        ini.set('äüü', 'äöü', ('ä', 'ö', 'ü'))
        ini.set('a', 'b', 5)
        self.assertEqual(ini['a'].getint('b'), 5)
        ini.set('a', 'c', None)
        self.assertNotIn('c', ini['a'])
        self.assertIn('ä\n', ini.write_string())
        self.assertEqual(len(ini.getlist('äüü', 'äöü')), 3)

        tmp = self.tmp_path('test')
        ini.write(tmp.as_posix())
        with tmp.open(encoding='utf8') as fp:
            res = fp.read()
        self.assertIn('coding: utf-8', res)

        ini2 = INI.from_file(tmp)
        self.assertEqual(ini2.write_string(), ini.write_string())
