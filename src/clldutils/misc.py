"""
This module provides miscellaneous utility functions, including backports of newer Python
functionality (:func:`lazyproperty`), formatting functions, etc.
"""

import re
import base64
import string
import typing
import pathlib
import warnings
import mimetypes
import unicodedata

__all__ = [
    'data_url', 'log_or_raise', 'nfilter', 'to_binary', 'dict_merged', 'NoDefault', 'NO_DEFAULT',
    'xmlchars', 'format_size', 'UnicodeMixin', 'slug', 'encoded', 'lazyproperty',
]


def deprecated(msg):
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
    warnings.simplefilter('default', DeprecationWarning)


def data_url(content: typing.Union[bytes, str, pathlib.Path], mimetype: str = None) -> str:
    """
    Returns content encoded as base64 Data URI. Useful to include (smallish) media resources
    in HTML pages.

    :param content: bytes or str or Path
    :param mimetype: mimetype of the content
    :return: `str` object (consisting only of ASCII, though)

    .. seealso:: https://en.wikipedia.org/wiki/Data_URI_scheme
    """
    if isinstance(content, pathlib.Path):
        if not mimetype:
            mimetype = mimetypes.guess_type(content.name)[0]
        with content.open('rb') as fp:
            content = fp.read()
    else:
        if isinstance(content, str):
            content = content.encode('utf8')
    return "data:{0};base64,{1}".format(
        mimetype or 'application/octet-stream', base64.b64encode(content).decode())


def log_or_raise(msg: str, log=None, level='warning', exception_cls=ValueError):
    """
    Utility for check procedures. If `log` is `None`, this works like `pytest -x`, otherwise
    the issue is just logged with the appropriate level.

    .. code-block:: python

        >>> from clldutils.misc import log_or_raise
        >>> log_or_raise("there's a problem")
        Traceback (most recent call last):
        ...
        ValueError: there's a problem
        >>> import logging
        >>> log_or_raise("there's a problem", log=logging.getLogger(__name__))
        there's a problem
    """
    if log:
        getattr(log, level)(msg)
    else:
        raise exception_cls(msg)


def nfilter(seq: typing.Iterable) -> list:
    """Replacement for python 2's filter(None, seq).

    :return: a list filtered from seq containing only truthy items.
    """
    return [e for e in seq if e]


def to_binary(s: typing.Union[str, bytes], encoding='utf8') -> bytes:
    """Cast function.

    :param s: object to be converted to bytes.
    """
    return s if isinstance(s, bytes) else bytes(s, encoding=encoding)


def dict_merged(d, _filter=None, **kw):
    """
    Update dictionary d with the items passed as kw if the value passes _filter.

    .. code-block:: python

        >>> from clldutils.misc import dict_merged
        >>> dict_merged({'a': 1}, b=2, c=3, _filter=lambda v: v > 2)
        {'a': 1, 'c': 3}
    """
    def f(s):
        if _filter:
            return _filter(s)
        return s is not None
    d = d or {}
    for k, v in kw.items():
        if f(v):
            d[k] = v
    return d


class NoDefault(object):

    def __repr__(self):
        return '<NoDefault>'


#: A singleton which can be used to distinguish no-argument-passed from None passed as
#: argument in callables with optional arguments.
NO_DEFAULT = NoDefault()


def xmlchars(text: str) -> str:
    """Not all of UTF-8 is considered valid character data in XML ...

    Thus, this function can be used to remove illegal characters from ``text``.

    .. seealso:: `<https://en.wikipedia.org/wiki/Valid_characters_in_XML>`_
    """
    invalid = list(range(0x9))
    invalid.extend([0xb, 0xc])
    invalid.extend(range(0xe, 0x20))
    return re.sub('|'.join('\\x%0.2X' % i for i in invalid), '', text)


def format_size(num: int) -> str:
    """Format byte-sizes for human readability.

    Cf. the `-h` option of the `du` command:

        -h, --human-readable print sizes in human readable format (e.g., 1K 234M 2G)

    :param num: Size given as number of bytes.

    .. seealso:: `<http://stackoverflow.com/a/1094933>`_
    """
    for x in ['bytes', 'KB', 'MB', 'GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


class UnicodeMixin(object):
    """Portable label mixin."""

    def __unicode__(self):
        """a human readable label for the object."""
        return '%s' % self  # pragma: no cover

    def __str__(self):
        """a human readable label for the object, appropriately encoded (or not)."""
        deprecated("Use of deprecated class UnicodeMixin! Use object instead.")
        return self.__unicode__()


def slug(s: str, remove_whitespace: bool = True, lowercase: bool = True) -> str:
    """
    Condenses a string to contain only (lowercase) alphanumeric characters.

    .. code-block:: python

        >>> from clldutils.misc import slug
        >>> slug('Some words!')
        'somewords'
        >>> slug('Some words!', lowercase=False)
        'Somewords'
        >>> slug('Some words!', remove_whitespace=False)
        'some words'
    """
    res = ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
    if lowercase:
        res = res.lower()
    for c in string.punctuation:
        res = res.replace(c, '')
    res = re.sub(r'\s+', '' if remove_whitespace else ' ', res)
    res = res.encode('ascii', 'ignore').decode('ascii')
    assert re.match('[ A-Za-z0-9]*$', res)
    return res


def encoded(string: typing.Union[str, bytes], encoding='utf-8') -> bytes:
    """Cast string to bytes in a specific encoding - with some guessing about the encoding.

    :param encoding: encoding which the object is forced to
    """
    assert isinstance(string, (str, bytes))
    if isinstance(string, str):
        return string.encode(encoding)
    try:
        # make sure the string can be decoded in the specified encoding ...
        string.decode(encoding)
        return string
    except UnicodeDecodeError:
        # ... if not use latin1 as best guess to decode the string before encoding as
        # specified.
        return string.decode('latin1').encode(encoding)


class lazyproperty(object):
    """Non-data descriptor caching the computed result as instance attribute.

    .. code-block:: python

        >>> class Spam(object):
        ...     @lazyproperty
        ...     def eggs(self):
        ...         return 'spamspamspam'
        >>> spam=Spam(); spam.eggs
        'spamspamspam'
        >>> spam.eggs='eggseggseggs'; spam.eggs
        'eggseggseggs'
        >>> Spam().eggs
        'spamspamspam'
        >>> Spam.eggs  # doctest: +ELLIPSIS
        <...lazyproperty object at 0x...>

    .. note::

        Since Python 3.8 added the `functools.cached_property` decorator
        (see `<https://docs.python.org/3/library/functools.html#functools.cached_property>`_),
        this function will be deprecated once Python 3.7 is no longer supported.
    """

    def __init__(self, fget):
        self.fget = fget
        for attr in ('__module__', '__name__', '__doc__'):
            setattr(self, attr, getattr(fget, attr))

    def __get__(self, instance, owner):
        if instance is None:
            return self
        result = instance.__dict__[self.__name__] = self.fget(instance)
        return result
