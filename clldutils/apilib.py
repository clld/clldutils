# coding: utf8
from __future__ import unicode_literals, print_function, division
from functools import partial
import json

import attr

from clldutils.misc import UnicodeMixin
from clldutils.path import git_describe, Path

# for backward compatibility:
from clldutils.attrlib import _valid_range as valid_range
from clldutils.attrlib import _valid_enum_member as valid_enum_member
from clldutils.attrlib import _valid_re as valid_re
assert valid_enum_member and valid_re


#
# Common attributes of data objects
#
def latitude():
    return attr.ib(
        convert=lambda s: None if s is None or s == '' else float(s),
        validator=partial(valid_range, -90, 90, nullable=True))


def longitude():
    return attr.ib(
        convert=lambda s: None if s is None or s == '' else float(s),
        validator=partial(valid_range, -180, 180, nullable=True))


def value_ascsv(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return "{0:.5f}".format(v)
    if isinstance(v, dict):
        return json.dumps(v)
    if isinstance(v, list):
        return ';'.join(v)
    return "{0}".format(v)


@attr.s
class DataObject(object):
    @classmethod
    def fieldnames(cls):
        return [f.name for f in attr.fields(cls)]

    def ascsv(self):
        res = []
        for f, v in zip(attr.fields(self.__class__), attr.astuple(self)):
            res.append((f.metadata.get('ascsv') or value_ascsv)(v))
        return res


class API(UnicodeMixin):
    """
    An API base class to provide programmatic access to data in a git repository.
    """
    # A light-weight way to specifiy a default repository location (without having to
    # overwrite __init__)
    __repos_path__ = None

    def __init__(self, repos=None):
        self.repos = Path(repos or self.__repos_path__)

    def __unicode__(self):
        name = self.repos.resolve().name if self.repos.exists() else self.repos.name
        return '<{0} repository {1} at {2}>'.format(
            name, git_describe(self.repos), self.repos)

    def path(self, *comps):
        return self.repos.joinpath(*comps)
