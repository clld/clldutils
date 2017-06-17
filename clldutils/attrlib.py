# coding: utf8
from __future__ import unicode_literals, print_function, division
from collections import OrderedDict
import re
from functools import partial

import attr

from clldutils.text import PATTERN_TYPE


def defaults(cls):
    res = OrderedDict()
    for field in attr.fields(cls):
        default = field.default
        if isinstance(default, attr.Factory):
            default = default.factory()
        res[field.name] = default
    return res


def asdict(obj, omit_defaults=True, omit_private=True):
    defs = defaults(obj.__class__)
    res = OrderedDict()
    for field in attr.fields(obj.__class__):
        if not (omit_private and field.name.startswith('_')):
            value = getattr(obj, field.name)
            if not (omit_defaults and value == defs[field.name]):
                if hasattr(value, 'asdict'):
                    value = value.asdict(omit_defaults=True)
                res[field.name] = value
    return res


def _valid_enum_member(choices, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and value not in choices:
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def _valid_range(min_, max_, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and (
            (min_ is not None and value < min_) or (max_ is not None and value > max_)):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_range(min_, max_, nullable=False):
    return partial(_valid_range, min_, max_, nullable=nullable)


def _valid_re(regex, instance, attribute, value, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(regex, PATTERN_TYPE):
        regex = re.compile(regex)
    if not regex.match(value):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_re(regex, nullable=False):
    return partial(_valid_re, regex, nullable=nullable)
