# coding: utf8
from __future__ import unicode_literals, print_function

from clldutils.testing import WithTempDir


class Tests(WithTempDir):
    def test_encoding(self):
        from clldutils.inifile import INI

        ini = self.tmp_path('test.ini')
        with ini.open('w', encoding='cp1252') as fp:
            fp.write('[äöü]\näöü = äöü')

        with self.assertRaises(UnicodeDecodeError):
            INI.from_file(ini)

        self.assertEqual(INI.from_file(ini, encoding='cp1252')['äöü']['äöü'], 'äöü')

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

        mt = '- a\n  - aa\n  - ab\n- b'
        ini.settext('text', 'multi', mt)

        tmp = self.tmp_path('test')
        ini.write(tmp.as_posix())
        with tmp.open(encoding='utf8') as fp:
            res = fp.read()
        self.assertIn('coding: utf-8', res)

        ini2 = INI.from_file(tmp)
        self.assertEqual(ini2.gettext('text', 'multi'), mt)
        self.assertEqual(ini2.write_string(), ini.write_string())
