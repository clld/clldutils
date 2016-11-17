# coding: utf8
from __future__ import unicode_literals
import re

from six import text_type

from clldutils.testing import WithTempDir, capture_all


class Tests(WithTempDir):
    def make_file(self, name):
        path = self.tmp_path(name)
        with path.open('w') as fp:
            fp.write('test')
        return path

    def test_import_module(self):
        from clldutils.path import import_module

        with self.tmp_path('__init__.py').open('w', encoding='ascii') as fp:
            fp.write('A = [1, 2, 3]')

        m = import_module(self.tmp_path())
        self.assertEqual(len(m.A), 3)

        with self.tmp_path('mod.py').open('w', encoding='ascii') as fp:
            fp.write('A = [1, 2, 3]')

        m = import_module(self.tmp_path('mod.py'))
        self.assertEqual(len(m.A), 3)

    def test_non_ascii(self):
        from clldutils.path import Path, path_component, as_unicode

        p = Path(path_component('äöü')).joinpath(path_component('äöü'))
        self.assertIsInstance(as_unicode(p), text_type)
        self.assertIsInstance(as_unicode(p.name), text_type)

    def test_as_posix(self):
        from clldutils.path import as_posix, Path

        self.assertRaises(ValueError, as_posix, 5)
        self.assertEquals(as_posix('.'), as_posix(Path('.')))

    def test_md5(self):
        from clldutils.path import md5

        self.assertIsNotNone(re.match('[a-f0-9]{32}$', md5(__file__)))

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
