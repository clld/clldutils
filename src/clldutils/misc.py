"""Generic utility functions."""

import re
import base64
import string
import pathlib
import warnings
import mimetypes
import unicodedata

from six import PY3, string_types, text_type, binary_type, iteritems

__all__ = [
    'data_url', 'log_or_raise', 'nfilter', 'to_binary', 'dict_merged', 'NoDefault', 'NO_DEFAULT',
    'xmlchars', 'format_size', 'UnicodeMixin', 'slug', 'encoded', 'lazyproperty',
]


def deprecated(msg):
    warnings.simplefilter('always', DeprecationWarning)
    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
    warnings.simplefilter('default', DeprecationWarning)


def data_url(content, mimetype=None):
    """
    Returns content encoded as base64 Data URI.

    :param content: bytes or str or Path
    :param mimetype: mimetype for
    :return: str object (consisting only of ASCII, though)

    .. seealso:: https://en.wikipedia.org/wiki/Data_URI_scheme
    """
    if isinstance(content, pathlib.Path):
        if not mimetype:
            mimetype = mimetypes.guess_type(content.name)[0]
        with content.open('rb') as fp:
            content = fp.read()
    else:
        if isinstance(content, text_type):
            content = content.encode('utf8')
    return "data:{0};base64,{1}".format(
        mimetype or 'application/octet-stream', base64.b64encode(content).decode())


def log_or_raise(msg, log=None, level='warning', exception_cls=ValueError):
    if log:
        getattr(log, level)(msg)
    else:
        raise exception_cls(msg)


def nfilter(seq):
    """Replacement for python 2's filter(None, seq).

    :return: a list filtered from seq containing only truthy items.
    """
    return [e for e in seq if e]


def to_binary(s, encoding='utf8'):
    """Portable cast function.

    In python 2 the ``str`` function which is used to coerce objects to bytes does not
    accept an encoding argument, whereas python 3's ``bytes`` function requires one.

    :param s: object to be converted to binary_type
    :return: binary_type instance, representing s.
    """
    if PY3:  # pragma: no cover
        return s if isinstance(s, binary_type) else binary_type(s, encoding=encoding)
    return binary_type(s)  # pragma: no cover


def dict_merged(d, _filter=None, **kw):
    """Update dictionary d with the items passed as kw if the value passes _filter."""
    def f(s):
        if _filter:
            return _filter(s)
        return s is not None
    d = d or {}
    for k, v in iteritems(kw):
        if f(v):
            d[k] = v
    return d


class NoDefault(object):

    def __repr__(self):
        return '<NoDefault>'


#: A singleton which can be used to distinguish no-argument-passed from None passed as
#: argument in callables with optional arguments.
NO_DEFAULT = NoDefault()


def xmlchars(text):
    """Not all of UTF-8 is considered valid character data in XML ...

    Thus, this function can be used to remove illegal characters from ``text``.
    """
    invalid = list(range(0x9))
    invalid.extend([0xb, 0xc])
    invalid.extend(range(0xe, 0x20))
    return re.sub('|'.join('\\x%0.2X' % i for i in invalid), '', text)


def format_size(num):
    """Format byte-sizes.

    .. seealso:: http://stackoverflow.com/a/1094933
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


def slug(s, remove_whitespace=True, lowercase=True):
    """Condensed version of s, containing only lowercase alphanumeric characters."""
    res = ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
    if lowercase:
        res = res.lower()
    for c in string.punctuation:
        res = res.replace(c, '')
    res = re.sub('\s+', '' if remove_whitespace else ' ', res)
    res = res.encode('ascii', 'ignore').decode('ascii')
    assert re.match('[ A-Za-z0-9]*$', res)
    return res


def encoded(string, encoding='utf-8'):
    """Cast string to binary_type.

    :param string: six.binary_type or six.text_type
    :param encoding: encoding which the object is forced to
    :return: six.binary_type
    """
    assert isinstance(string, string_types) or isinstance(string, binary_type)
    if isinstance(string, text_type):
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
