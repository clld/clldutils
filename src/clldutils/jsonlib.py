import re
import json
import pathlib
import datetime
import contextlib
import collections

import dateutil.parser

DATETIME_ISO_FORMAT = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+')


def parse(d):
    """Convert iso formatted timestamps found as values in the dict d to datetime objects.

    :return: A shallow copy of d with converted timestamps.
    """
    res = {}
    for k, v in d.items():
        if isinstance(v, str) and DATETIME_ISO_FORMAT.match(v):
            v = dateutil.parser.parse(v)
        res[k] = v
    return res


def format(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def dump(obj, path, **kw):
    """json.dump which understands filenames.

    :param obj: The object to be dumped.
    :param path: The path of the JSON file to be written.
    :param kw: Keyword parameters are passed to json.dump
    """
    # avoid indented lines ending with ", " on PY2
    if kw.get('indent') and kw.get('separators') is None:
        kw['separators'] = (',', ': ')

    with pathlib.Path(path).open('w', encoding='utf-8') as fp:
        return json.dump(obj, fp, **kw)


def load(path, **kw):
    """json.load which understands filenames.

    :param kw: Keyword parameters are passed to json.load
    :return: The python object read from path.
    """
    with pathlib.Path(path).open(encoding='utf-8') as fp:
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
    return update(
        path,
        default=collections.OrderedDict(),
        load_kw=dict(object_pairs_hook=collections.OrderedDict),
        **kw)
