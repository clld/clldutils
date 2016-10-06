# coding: utf8
from __future__ import unicode_literals

from clldutils.testing import WithTempDir, capture_all


class Tests(WithTempDir):
    def make_file(self, name):
        path = self.tmp_path(name)
        with path.open('w') as fp:
            fp.write('test')
        return path

    def test_as_posix(self):
        from clldutils.path import as_posix, Path

        self.assertRaises(ValueError, as_posix, 5)
        self.assertEquals(as_posix('.'), as_posix(Path('.')))

    def test_copytree(self):
        from clldutils.path import copytree

        dst = self.tmp_path('a', 'b')
        copytree(self.tmp_path(), dst)
        self.assertTrue(dst.exists())
        self.assertRaises(OSError, copytree, dst, dst)

    def test_copy(self):
        from clldutils.path import copy

        src = self.make_file('test')
        dst = self.tmp_path('other')
        copy(src, dst)
        self.assertEquals(src.stat().st_size, dst.stat().st_size)

    def test_move(self):
        from clldutils.path import move

        dst = self.tmp_path('a')
        dst.mkdir()
        src = self.make_file('test')
        move(src, dst)
        self.assertFalse(src.exists())
        self.assertTrue(dst.joinpath(src.name).exists())

    def test_remove(self):
        from clldutils.path import remove

        self.assertRaises(OSError, remove, self.tmp_path('nonexistingpath'))
        tmp = self.make_file('test')
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

    def test_walk(self):
        from clldutils.path import walk

        d = self.tmp_path('testdir')
        d.mkdir()
        self.make_file('testfile')
        res = [p.name for p in walk(self.tmp_path(), mode='files')]
        self.assertNotIn('testdir', res)
        self.assertIn('testfile', res)
        res = [p.name for p in walk(self.tmp_path(), mode='dirs')]
        self.assertIn('testdir', res)
        self.assertNotIn('testfile', res)

    def test_git_describe(self):
        from clldutils.path import git_describe

        d = self.tmp_path('testdir')
        self.assertRaises(ValueError, git_describe, d)
        d.mkdir()
        with capture_all(git_describe, d) as res:
            self.assertEqual(res[0], 'testdir')

    def test_TemporaryDirectory(self):
        from clldutils.path import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            assert tmp.exists()
        assert not tmp.exists()
