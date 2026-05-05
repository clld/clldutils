import re
import sys
import shutil
import warnings

import pytest

from clldutils.path import Path, Manifest, memorymapped


def make_file(d, name='test.txt', text='test', encoding='utf-8'):
    path = d / name
    path.write_text(text, encoding=encoding)
    return path


def test_Manifest(tmp_path):
    d = Path(__file__).parent
    m = {k: v for k, v in Manifest.from_dir(d).items()}
    shutil.copytree(d, tmp_path / 'd')
    assert m == Manifest.from_dir(tmp_path / 'd')
    shutil.copytree(d, tmp_path / 'd' / 'd')
    assert m != Manifest.from_dir(tmp_path / 'd')


def test_Manifest2(tmp_path):
    make_file(tmp_path, name='b.txt')
    make_file(tmp_path, name='a.txt')
    m = Manifest.from_dir(tmp_path)
    assert '{0}'.format(m) == \
        '098f6bcd4621d373cade4e832627b4f6  a.txt\n098f6bcd4621d373cade4e832627b4f6  b.txt'
    m.write(Path(tmp_path))
    assert tmp_path.joinpath('manifest-md5.txt').exists()


def test_memorymapped(tmp_path):
    p = make_file(tmp_path, text='äöü', encoding='utf-8')
    with memorymapped(p) as b:
        assert b.find('ö'.encode('utf-8')) == 2


def test_readlines(tmp_path):
    from clldutils.path import readlines

    # Test files are read using universal newline mode:
    tpath = tmp_path / 'test.txt'
    tpath.write_bytes(b'a\nb\r\nc\rd')
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


def test_import_module(tmp_path):
    from clldutils.path import import_module

    make_file(tmp_path, name='__init__.py', text='A = [1, 2, 3]')
    syspath = sys.path[:]
    m = import_module(tmp_path)
    assert len(m.A) == 3
    assert syspath == sys.path

    make_file(tmp_path, name='abcd.py', text='A = [1, 2, 3]')
    m = import_module(tmp_path / 'abcd.py')
    assert len(m.A) == 3


def test_as_posix():
    from clldutils.path import as_posix, Path

    with pytest.raises(ValueError):
        as_posix(5)
    assert as_posix('.') == as_posix(Path('.'))


def test_md5():
    from clldutils.path import md5

    assert re.match('[a-f0-9]{32}$', md5(__file__))


def test_walk(tmp_path):
    from clldutils.path import walk

    d = tmp_path / 'testdir'
    d.mkdir()
    make_file(tmp_path, name='testfile')
    res = [p.name for p in walk(d.parent, mode='files')]
    assert 'testdir' not in res
    assert 'testfile' in res
    res = [p.name for p in walk(d.parent, mode='dirs')]
    assert 'testdir' in res
    assert 'testfile' not in res


def test_git_describe(tmp_path, capsys):
    from clldutils.path import git_describe

    d = tmp_path / 'testdir'
    with pytest.raises(ValueError):
        git_describe(d)
    d.mkdir()
    assert git_describe(d) == 'testdir'


def test_ensure_cmd():
    from clldutils.path import ensure_cmd

    with pytest.raises(ValueError) as e:
        ensure_cmd('this-command-is-not-installed')
    assert 'this-command' in str(e)


def test_TemporaryDirectory():
    from clldutils.path import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        assert tmp.exists()
    assert not tmp.exists()
