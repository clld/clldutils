from datetime import date

import pytest

from clldutils.jsonlib import dump, load, parse, update, format, update_ordered


def test_parse_json_with_datetime():
    assert parse(dict(d='2012-12-12T20:12:12.12'))['d'].year


def test_update(tmppath):
    p = tmppath / 'test'
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


def test_update_ordered(tmppath):
    p = tmppath / 'test'

    with update_ordered(p) as obj:
        obj['b'] = 2
        obj['a'] = 1

    with update_ordered(p) as obj:
        assert list(obj.keys()) == ['b', 'a']


def test_json(tmppath):
    d = {'a': 234, 'ä': 'öäüß'}
    p = tmppath / 'test'
    dump(d, p, indent=4)
    for k, v in load(p).items():
        assert d[k] == v


def test_format_json():
    format(date.today())
    assert format(5) == 5
