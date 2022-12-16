from datetime import date

import pytest

from clldutils.jsonlib import dump, load, parse, update, format, update_ordered


def test_parse_json_with_datetime():
    assert parse(dict(d='2012-12-12T20:12:12.12'))['d'].year
    assert parse(dict(d=dict(c='2012-12-12T20:12:12.12')))['d']['c'].year
    assert parse(dict(d=['2012-12-12T20:12:12.12']))['d'][0].year


def test_update(tmp_path):
    p = tmp_path / 'test'
    with pytest.raises(ValueError):
        with update(p):
            pass  # pragma: no cover

    with update(p, default={}) as obj:
        obj['a'] = 1

    with update(p) as obj:
        assert obj['a'] == 1
        obj['a'] = 2

    with update(p) as obj:
        assert obj['a'] == 2


def test_update_ordered(tmp_path):
    p = tmp_path / 'test'

    with update_ordered(p) as obj:
        obj['b'] = 2
        obj['a'] = 1

    with update_ordered(p) as obj:
        assert list(obj.keys()) == ['b', 'a']


def test_json(tmp_path):
    d = {'a': 234, 'ä': 'öäüß'}
    p = tmp_path / 'test'
    dump(d, p, indent=4)
    for k, v in load(p).items():
        assert d[k] == v
    with tmp_path.joinpath('test.js').open('w', encoding='utf8') as fp:
        dump(d, fp)
    with tmp_path.joinpath('test.js').open('r', encoding='utf8') as fp:
        assert load(fp) == d


def test_format_json():
    format(date.today())
    assert format(5) == 5
