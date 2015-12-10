# coding: utf8
from __future__ import unicode_literals

from clldutils.testing import WithTempDir


class Tests(WithTempDir):
    def test_as_posix(self):
        from clldutils.path import as_posix, Path

        self.assertRaises(ValueError, as_posix, 5)
        self.assertEquals(as_posix('.'), as_posix(Path('.')))

    def test_remove(self):
        from clldutils.path import remove

        self.assertRaises(OSError, remove, self.tmp_path('nonexistingpath'))
        tmp = self.tmp_path('test')
        with tmp.open('w') as fp:
            fp.write('test')
        self.assertTrue(tmp.exists())
        remove(tmp)
        self.assertFalse(tmp.exists())

    def test_rmtree(self):
        from clldutils.path import rmtree

        self.assertRaises(OSError, rmtree, self.tmp_path('nonexistingpath'))
        rmtree(self.tmp_path('nonexistingpath'), ignore_errors=True)
        tmp = self.tmp_path('test')
        tmp.mkdir()
        self.assertTrue(tmp.exists())
        rmtree(tmp)
        self.assertFalse(tmp.exists())
