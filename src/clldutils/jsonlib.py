from __future__ import unicode_literals

import re
import json
import contextlib
from datetime import date, datetime
from collections import OrderedDict

from six import PY3, string_types, iteritems

import dateutil.parser

from clldutils._compat import pathlib

DATETIME_ISO_FORMAT = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+')


def parse(d):
    """Convert iso formatted timestamps found as values in the dict d to datetime objects.

    :return: A shallow copy of d with converted timestamps.
    """
    res = {}
    for k, v in iteritems(d):
        if isinstance(v, string_types) and DATETIME_ISO_FORMAT.match(v):
            v = dateutil.parser.parse(v)
        res[k] = v
    return res


def format(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def dump(obj, path, **kw):
    """Python 2 + 3 compatible version of json.dump.

    :param obj: The object to be dumped.
    :param path: The path of the JSON file to be written.
    :param kw: Keyword parameters are passed to json.dump
    """
    open_kw = {'mode': 'w'}
    if PY3:  # pragma: no cover
        open_kw['encoding'] = 'utf-8'

    # avoid indented lines ending with ", " on PY2
    if kw.get('indent') and kw.get('separators') is None:
        kw['separators'] = (',', ': ')

    with open(str(path), **open_kw) as fp:
        return json.dump(obj, fp, **kw)


def load(path, **kw):
    """python 2 + 3 compatible version of json.load.

    :param kw: Keyword parameters are passed to json.load
    :return: The python object read from path.
    """
    _kw = {}
    if PY3:  # pragma: no cover
        _kw['encoding'] = 'utf-8'
    with open(str(path), **_kw) as fp:
        return json.load(fp, **kw)


@contextlib.contextmanager
def update(path, default=None, load_kw=None, **kw):
    path = pathlib.Path(path)
    if not path.exists():
        if default is None:
            raise ValueError('path does not exist')
        res = default
    else:
        res = load(path, **(load_kw or {}))
    yield res
    dump(res, path, **kw)


def update_ordered(path, **kw):
    return update(path, default=OrderedDict(), load_kw=dict(object_pairs_hook=OrderedDict), **kw)
