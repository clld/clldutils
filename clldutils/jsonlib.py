# coding: utf8
from __future__ import unicode_literals
import json
import re
from contextlib import contextmanager
from datetime import date, datetime

from six import PY3, string_types
import dateutil.parser

from clldutils.path import as_posix, Path


DATETIME_ISO_FORMAT = re.compile(
    '[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}\:[0-9]{2}\:[0-9]{2}\.[0-9]+')


def parse(d):
    """
    convert iso formatted timestamps found as values in the dict d to datetime objects.

    :return: A shallow copy of d with converted timestamps.
    """
    res = {}
    for k, v in d.items():
        if isinstance(v, string_types) and DATETIME_ISO_FORMAT.match(v):
            v = dateutil.parser.parse(v)
        res[k] = v
    return res


def format(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def dump(obj, path, **kw):
    """python 2 + 3 compatible version of json.dump.

    :param obj: The object to be dumped.
    :param path: The path of the JSON file to be written.
    :param kw: Keyword parameters are passed to json.dump
    """
    _kw = dict(mode='w')
    if PY3:  # pragma: no cover
        _kw['encoding'] = 'utf8'
    with open(as_posix(path), **_kw) as fp:
        return json.dump(obj, fp, **kw)


def load(path, **kw):
    """python 2 + 3 compatible version of json.load.

    :param kw: Keyword parameters are passed to json.load
    :return: The python object read from path.
    """
    _kw = {}
    if PY3:  # pragma: no cover
        _kw['encoding'] = 'utf8'
    with open(as_posix(path), **_kw) as fp:
        return json.load(fp, **kw)


@contextmanager
def update(path, default=None, **kw):
    path = Path(path)
    if not path.exists():
        if default is None:
            raise ValueError('path does not exist')
        res = default
    else:
        res = load(path)
    yield res
    dump(res, path, **kw)
