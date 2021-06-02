import pytest
from clldutils.inifile import INI


def test_encoding(tmp_path):
    ini = tmp_path / 'test.ini'
    ini.write_text('[äöü]\näöü = äöü', encoding='cp1252')

    with pytest.raises(UnicodeDecodeError):
        INI.from_file(ini)

    assert INI.from_file(ini, encoding='cp1252')['äöü']['äöü'] == 'äöü'


def test_INI(tmp_path):
    ini = INI()
    ini.set('äüü', 'äöü', ('ä', 'ö', 'ü'))
    ini.set('a', 'b', 5)
    assert ini['a'].getint('b') == 5
    ini.set('a', 'c', None)
    assert 'c' not in ini['a']
    assert 'ä\n' in ini.write_string()
    assert len(ini.getlist('äüü', 'äöü')) == 3

    mt = '- a\n  - aa\n  - ab\n- b'
    ini.settext('text', 'multi', mt)

    tmp = tmp_path / 'test'
    ini.write(tmp.as_posix())
    with tmp.open(encoding='utf8') as fp:
        res = fp.read()
    assert 'coding: utf-8' in res

    ini2 = INI.from_file(tmp)
    assert ini2.gettext('text', 'multi') == mt
    assert ini2.write_string() == ini.write_string()
