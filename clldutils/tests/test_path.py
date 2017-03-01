# coding: utf8
from __future__ import unicode_literals
import re
import sys

from six import text_type

from clldutils.testing import WithTempDir, capture_all


class Tests(WithTempDir):
    def make_file(self, name='test.txt', text='test'):
        path = self.tmp_path(name)
        with path.open('w') as fp:
            fp.write(text)
        return path

    def test_Manifest(self):
        from clldutils.path import Manifest, copytree, Path

        d = Path(__file__).parent
        m = {k: v for k, v in Manifest.from_dir(d).items()}
        copytree(d, self.tmp_path('d'))
        self.assertEqual(m, Manifest.from_dir(self.tmp_path('d')))
        copytree(d, self.tmp_path('d', 'd'))
        self.assertNotEqual(m, Manifest.from_dir(self.tmp_path('d')))

    def test_Manifest2(self):
        from clldutils.path import Manifest
        self.make_file(name='b.txt')
        self.make_file(name='a.txt')
        m = Manifest.from_dir(self.tmp_path())
        self.assertEqual(
            '{0}'.format(m),
            '098f6bcd4621d373cade4e832627b4f6  a.txt\n'
            '098f6bcd4621d373cade4e832627b4f6  b.txt')
        m.write(self.tmp_path())
        self.assertTrue(self.tmp_path('manifest-md5.txt').exists())

    def test_memorymapped(self):
        from clldutils.path import memorymapped

        p = self.make_file(text='äöü')
        with memorymapped(p) as b:
            self.assertEqual(b.find('ö'.encode('utf8')), 2)

    def test_read_write(self):
        from clldutils.path import read_text, write_text

        text = 'äöüß'
        p = self.tmp_path('test')
        self.assertEqual(write_text(p, text), len(text))
        self.assertEqual(read_text(p), text)

    def test_readlines(self):
        from clldutils.path import readlines

        # Test files are read using universal newline mode:
        fname = self.make_file(text='a\nb\r\nc\rd')
        self.assertEqual(len(readlines(fname)), 4)

        lines = ['\t#ä ']
        self.assertEqual(readlines(lines), lines)
        self.assertNotEqual(readlines(lines, normalize='NFD'), lines)
        self.assertEqual(readlines(lines, strip=True)[0], lines[0].strip())
        self.assertEqual(readlines(lines, comment='#'), [])
        self.assertEqual(readlines(lines, comment='#', linenumbers=True), [(1, None)])
        lines = ['']
        self.assertEqual(readlines(lines), [''])
        self.assertEqual(readlines(lines, comment='#'), [])
        self.assertEqual(readlines(lines, strip=True, normalize='NFC'), [])

    def test_import_module(self):
        from clldutils.path import import_module

        with self.tmp_path('__init__.py').open('w', encoding='ascii') as fp:
            fp.write('A = [1, 2, 3]')

        syspath = sys.path[:]
        m = import_module(self.tmp_path())
        self.assertEqual(len(m.A), 3)
        self.assertEqual(syspath, sys.path)

        with self.tmp_path('abcd.py').open('w', encoding='ascii') as fp:
            fp.write('A = [1, 2, 3]')

        m = import_module(self.tmp_path('abcd.py'))
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
