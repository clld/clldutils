"""
This module provides small tools to make reading and writing JSON data simpler. The standard
library's `json` module does all the heavy lifting here, but some shortcomings are addressed.

One of these shortcomings is missing support for `datetime` objects. This can be remedied using the
functions :func:`format` and :func:`parse` as follows:

.. code-block:: python

    >>> from datetime import datetime
    >>> from clldutils.jsonlib import parse, format
    >>> from json import JSONEncoder, loads, dumps
    >>> class DateTimeEncoder(JSONEncoder):
    ...     def default(self, obj):
    ...         return format(obj)
    ...
    >>> dumps({'start': datetime.now(), 'end': 5}, cls=DateTimeEncoder)
    '{"start": "2022-12-15T14:32:45.637522", "end": 5}'
    >>> parse(json.loads(json.dumps({'start': datetime.now(), 'end': 5}, cls=DateTimeEncoder)))
    {'start': datetime.datetime(2022, 12, 15, 14, 33, 17, 323973), 'end': 5}
"""
import re
import json
import pathlib
import datetime
import contextlib
import collections
import typing

import dateutil.parser

__all__ = ['parse', 'format', 'dump', 'load', 'update', 'update_ordered']

DATETIME_ISO_FORMAT = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+')


def parse(d: dict) -> dict:
    """
    Convert iso formatted timestamps found as values in the dict d to datetime objects.

    .. note:: This works with nested `dict`s and `list` values, too.

    .. code-block:: python

        >>> parse({"start": {'from': "2022-12-15T14:32:45.637522", 'to': 7}})['start']['from']
        datetime.datetime(2022, 12, 15, 14, 32, 45, 637522)
        >>> parse({"start": ["2022-12-15T14:32:45.637522"]})['start'][0]
        datetime.datetime(2022, 12, 15, 14, 32, 45, 637522)

    :return: A shallow copy of d with converted timestamps.
    """
    res = {}
    for k, v in d.items():
        if isinstance(v, str) and DATETIME_ISO_FORMAT.match(v):
            v = dateutil.parser.parse(v)
        elif isinstance(v, dict):
            v = parse(v)
        elif isinstance(v, list):
            v = [
                dateutil.parser.parse(vv)
                if isinstance(vv, str) and DATETIME_ISO_FORMAT.match(vv) else vv
                for vv in v]
        res[k] = v
    return res


def format(value):
    """
    Format a value as ISO timestamp if it is a datetime.date(time) instance, otherwise return it
    unchanged.
    """
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def dump(obj, path: typing.Union[typing.TextIO, str, pathlib.Path], **kw):
    """`json.dump` which understands filenames.

    :param obj: The object to be dumped.
    :param path: The path of the JSON file to be written.
    :param kw: Keyword parameters are passed to json.dump
    """
    if isinstance(path, (str, pathlib.Path)):
        with pathlib.Path(path).open('w', encoding='utf-8') as fp:
            return json.dump(obj, fp, **kw)
    return json.dump(obj, path, **kw)


def load(path: typing.Union[typing.TextIO, str, pathlib.Path], **kw):
    """`json.load` which understands filenames.

    :param kw: Keyword parameters are passed to json.load
    :return: The python object read from path.
    """
    if isinstance(path, (str, pathlib.Path)):
        with pathlib.Path(path).open(encoding='utf-8') as fp:
            return json.load(fp, **kw)
    return json.load(path, **kw)


@contextlib.contextmanager
def update(path, default=None, load_kw=None, **kw):
    """
    An update-able JSON file

    .. code-block:: python

        >>> with update('/tmp/t.json', default={}) as o:
        ...     o['x'] = 5
        ...
        >>> load('/tmp/t.json')['x']
        5
    """
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
    return update(
        path,
        default=collections.OrderedDict(),
        load_kw=dict(object_pairs_hook=collections.OrderedDict),
        **kw)
