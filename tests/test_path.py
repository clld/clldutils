# coding: utf8
from __future__ import unicode_literals
import re
import sys
import warnings

from six import text_type
import pytest

from clldutils.path import Path, Manifest, copytree, memorymapped


def make_file(d, name='test.txt', text='test', encoding='utf-8'):
    path = d / name
    path.write_text(text, encoding=encoding)
    return path


def test_Manifest(tmppath):
    d = Path(__file__).parent
    m = {k: v for k, v in Manifest.from_dir(d).items()}
    copytree(d, tmppath / 'd')
    assert m == Manifest.from_dir(tmppath / 'd')
    copytree(d, tmppath / 'd' / 'd')
    assert m != Manifest.from_dir(tmppath / 'd')


def test_Manifest2(tmppath):
    make_file(tmppath, name='b.txt')
    make_file(tmppath, name='a.txt')
    m = Manifest.from_dir(tmppath)
    assert '{0}'.format(m) == \
        '098f6bcd4621d373cade4e832627b4f6  a.txt\n098f6bcd4621d373cade4e832627b4f6  b.txt'
    m.write(Path(tmppath))
    assert tmppath.joinpath('manifest-md5.txt').exists()


def test_memorymapped(tmppath):
    p = make_file(tmppath, text='äöü', encoding='utf-8')
    with memorymapped(p) as b:
        assert b.find('ö'.encode('utf-8')) == 2


def test_read_write(tmppath, recwarn):
    from clldutils.path import read_text, write_text

    warnings.simplefilter("always")
    text = 'äöüß'
    p = tmppath / 'test'
    assert write_text(p, text) == len(text)
    assert read_text(p) == text
    assert recwarn.pop(DeprecationWarning)
    warnings.simplefilter("default")


def test_readlines(tmpdir):
    from clldutils.path import readlines

    # Test files are read using universal newline mode:
    tpath = tmpdir / 'test.txt'
    tpath.write_binary(b'a\nb\r\nc\rd')
    assert len(readlines(str(tpath))) == 4

    lines = ['\t#ä ']
    assert readlines(lines) == lines
    assert readlines(lines, normalize='NFD') != lines
    assert readlines(lines, strip=True)[0] == lines[0].strip()
    assert readlines(lines, comment='#') == []
    assert readlines(lines, comment='#', linenumbers=True) == [(1, None)]
    lines = ['']
    assert readlines(lines) == ['']
    assert readlines(lines, comment='#') == []
    assert readlines(lines, strip=True, normalize='NFC') == []


def test_import_module(tmppath):
    from clldutils.path import import_module

    make_file(tmppath, name='__init__.py', text='A = [1, 2, 3]')
    syspath = sys.path[:]
    m = import_module(tmppath)
    assert len(m.A) == 3
    assert syspath == sys.path

    make_file(tmppath, name='abcd.py', text='A = [1, 2, 3]')
    m = import_module(tmppath / 'abcd.py')
    assert len(m.A) == 3


def test_non_ascii(recwarn):
    from clldutils.path import Path, path_component, as_unicode

    assert path_component(b'abc') == 'abc'

    warnings.simplefilter("always")
    p = Path(path_component('äöü')).joinpath(path_component('äöü'))
    assert isinstance(as_unicode(p), text_type)
    assert isinstance(as_unicode(p.name), text_type)
    assert recwarn.pop(DeprecationWarning)
    warnings.simplefilter("default")


def test_as_posix():
    from clldutils.path import as_posix, Path

    with pytest.raises(ValueError):
        as_posix(5)
    assert as_posix('.') == as_posix(Path('.'))


def test_md5():
    from clldutils.path import md5

    assert re.match('[a-f0-9]{32}$', md5(__file__))


def test_copytree(tmppath):
    from clldutils.path import copytree

    dst = tmppath / 'a' / 'b'
    copytree(tmppath, dst)
    assert dst.exists()
    with pytest.raises(OSError):
        copytree(dst, dst)


def test_copy(tmppath):
    from clldutils.path import copy

    src = make_file(tmppath, name='test', text='abc')
    dst = tmppath / 'other'
    copy(src, dst)
    assert src.stat().st_size == dst.stat().st_size


def test_move(tmppath):
    from clldutils.path import move

    dst = tmppath / 'a'
    dst.mkdir()
    src = make_file(tmppath, name='test')
    move(src, dst)
    assert not src.exists()
    assert dst.joinpath(src.name).exists()


def test_remove(tmppath, recwarn):
    from clldutils.path import remove

    warnings.simplefilter("always")
    with pytest.raises(OSError):
        remove(tmppath / 'nonexistingpath')
    tmp = make_file(tmppath, name='test')
    assert tmp.exists()
    remove(tmp)
    assert not tmp.exists()
    assert recwarn.pop(DeprecationWarning)
    warnings.simplefilter("default")


def test_rmtree(tmppath):
    from clldutils.path import rmtree

    with pytest.raises(OSError):
        rmtree(tmppath / 'nonexistingpath')
    rmtree(tmppath / 'nonexistingpath', ignore_errors=True)
    tmp = tmppath / 'test'
    tmp.mkdir()
    assert tmp.exists()
    rmtree(tmp)
    assert not tmp.exists()


def test_walk(tmppath):
    from clldutils.path import walk

    d = tmppath / 'testdir'
    d.mkdir()
    make_file(tmppath, name='testfile')
    res = [p.name for p in walk(d.parent, mode='files')]
    assert 'testdir' not in res
    assert 'testfile' in res
    res = [p.name for p in walk(d.parent, mode='dirs')]
    assert 'testdir' in res
    assert 'testfile' not in res


def test_git_describe(tmppath, capsys):
    from clldutils.path import git_describe

    d = tmppath / 'testdir'
    with pytest.raises(ValueError):
        git_describe(d)
    d.mkdir()
    assert git_describe(d) == 'testdir'


def test_TemporaryDirectory():
    from clldutils.path import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        assert tmp.exists()
    assert not tmp.exists()
