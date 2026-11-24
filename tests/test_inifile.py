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


@pytest.mark.parametrize('default_section', ['DEFAULT', 'shared'])
def test_default_section(tmp_path, default_section):
    count = 5
    ini = INI(default_section=default_section)
    ini.set(default_section, 'language', 'en')
    ini.set(default_section, 'count', count)
    ini.set(default_section, 'languages', ['en', 'de'])
    ini.set('record', 'title', 'Example')

    assert ini.sections() == ['record']
    assert ini.get('record', 'language') == 'en'
    assert ini.getint('record', 'count') == count
    assert ini.getlist('record', 'languages') == ['en', 'de']

    path = tmp_path / 'defaults.ini'
    ini.write(path)
    restored = INI.from_file(path, default_section=default_section)
    assert restored.sections() == ['record']
    assert restored.defaults() == ini.defaults()
    assert restored.get('record', 'language') == 'en'
    assert restored.getlist('record', 'languages') == ['en', 'de']


@pytest.mark.parametrize('default_section', ['DEFAULT', 'shared'])
def test_constructor_and_dict_defaults(default_section):
    count = 5
    ini = INI(defaults={'language': 'en'}, default_section=default_section)
    ini.read_dict({default_section: {'count': count}, 'record': {'title': 'Example'}})

    assert ini.defaults() == {'language': 'en', 'count': str(count)}
    assert ini.sections() == ['record']
    assert ini.get('record', 'language') == 'en'
    assert ini.getint('record', 'count') == count

    ini.set('record', 'language', 'de')
    assert ini.get('record', 'language') == 'de'
    assert ini.defaults()['language'] == 'en'
