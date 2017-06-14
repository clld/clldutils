# coding: utf8
from __future__ import unicode_literals, print_function, division
import re
from functools import partial
import json

import attr

from clldutils.misc import UnicodeMixin
from clldutils.path import git_describe, Path
from clldutils.text import PATTERN_TYPE


#
# Functionality for simpler creation of models using the attrs library
#
# Validators can be obtained from basic building blocks by parametrizing the base
# functions using functools.partial.
#
def valid_enum_member(choices, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and value not in choices:
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_range(min_, max_, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and (
            (min_ is not None and value < min_) or (max_ is not None and value > max_)):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_re(regex, instance, attribute, value, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(regex, PATTERN_TYPE):
        regex = re.compile(regex)
    if not regex.match(value):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


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
