# coding: utf8
from __future__ import unicode_literals
from datetime import date

import pytest

from clldutils.jsonlib import dump, load, parse, update, format


def test_parse_json_with_datetime():
    assert parse(dict(d='2012-12-12T20:12:12.12'))['d'].year


def test_update(tmpdir):
    p = str(tmpdir.join('test'))
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


def test_json(tmpdir):
    d = {'a': 234, 'ä': 'öäüß'}
    p = str(tmpdir.join('test'))
    dump(d, p, indent=4)
    for k, v in load(p).items():
        assert d[k] == v


def test_format_json():
    format(date.today())
    assert format(5) == 5
