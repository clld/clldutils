"""
Data curation can profit a lot from a transparent data model and documented structure. This can be
achieved using the `attrs` library,

- defining core objects of the data as `@attr.s` decorated classes
- using `attrs` validation and conversion functionality, to observe the principle of locality - \
  i.e. have data cleanup defined close to the objects, while accessing clean data through the \
  objects elsewhere in the code base.
"""
import re
import functools
import collections

import attr

from clldutils.text import PATTERN_TYPE
from clldutils.misc import deprecated

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
    """
    Enhanced version of `attr.asdict`.

    :param omit_defaults: If `True`, only attribute values which differ from the default will be \
    added.
    :param omit_private: If `True`, values of private attributes (i.e. attributes with names \
    starting with `_`) will not be added.

    .. code-block:: python

        >>> @attr.s
        ... class Bag:
        ...     _private = attr.ib()
        ...     with_default = attr.ib(default=7)
        ...
        >>> asdict(Bag('x'))
        OrderedDict()
        >>> asdict(Bag('x'), omit_defaults=False, omit_private=False)
        OrderedDict([('_private', 'x'), ('with_default', 7)])
        >>> attr.asdict(Bag('x'))
        {'_private': 'x', 'with_default': 7}

    """
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
    """
    .. deprecated:: 3.9
        Use `attr.validators.in_` instead.
    """
    deprecated('Use `attr.validators.in_` instead.')
    return functools.partial(_valid_enum_member, choices, nullable=nullable)


def _valid_range(min_, max_, instance, attribute, value, nullable=False):
    if not (nullable and value is None) and (
            (min_ is not None and value < min_) or (max_ is not None and value > max_)):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_range(min_, max_, nullable=False):
    """
    A validator that raises a `ValueError` if the provided value that is not in the range defined
    by `min_` and `max_`.
    """
    return functools.partial(_valid_range, min_, max_, nullable=nullable)


def _valid_re(regex, instance, attribute, value, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(regex, PATTERN_TYPE):
        regex = re.compile(regex)
    if not regex.match(value):
        raise ValueError('{0} is not a valid {1}'.format(value, attribute.name))


def valid_re(regex, nullable=False):
    """
    .. deprecated:: 3.9
        Use `attr.validators.matches_re` instead.
    """
    deprecated('Use `attr.validators.matches_re` instead.')
    return functools.partial(_valid_re, regex, nullable=nullable)
