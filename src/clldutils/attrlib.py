import re
import functools
import collections

import attr

from clldutils.text import PATTERN_TYPE

__all__ = ['asdict', 'valid_range', 'valid_re', 'valid_enum_member', 'cmp_off']

# Avoid deprecation warnings for "cmp=False"
# See https://www.attrs.org/en/stable/api.html#deprecated-apis
if getattr(attr, "__version_info__", (0,)) >= (19, 2):
    cmp_off = {"eq": False}
else:  # pragma: no cover
    cmp_off = {"cmp": False}


def defaults(cls):
    res = collections.OrderedDict()
    for field in attr.fields(cls):
        default = field.default
        if isinstance(default, attr.Factory):
            default = default.factory()
        res[field.name] = default
    return res


def asdict(obj, omit_defaults=True, omit_private=True):
    defs = defaults(obj.__class__)
    res = collections.OrderedDict()
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


def valid_enum_member(choices, nullable=False):
    return functools.partial(_valid_enum_member, choices, nullable=nullable)


def _valid_range(min_, max_, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and (
            (min_ is not None and value < min_) or (max_ is not None and value > max_)):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_range(min_, max_, nullable=False):
    return functools.partial(_valid_range, min_, max_, nullable=nullable)


def _valid_re(regex, instance, attribute, value, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(regex, PATTERN_TYPE):
        regex = re.compile(regex)
    if not regex.match(value):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_re(regex, nullable=False):
    return functools.partial(_valid_re, regex, nullable=nullable)
