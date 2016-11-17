"""Generic utility functions."""
from __future__ import unicode_literals, print_function, division, absolute_import
import re
import unicodedata
import string
import keyword
from string import ascii_letters

from six import PY3, string_types, text_type, binary_type


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
    return binary_type(s)


def dict_merged(d, _filter=None, **kw):
    """Update dictionary d with the items passed as kw if the value passes _filter."""
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

    if PY3:  # pragma: no cover
        def __str__(self):
            """a human readable label for the object, appropriately encoded (or not)."""
            return self.__unicode__()
    else:
        def __str__(self):
            """a human readable label for the object, appropriately encoded (or not)."""
            return self.__unicode__().encode('utf-8')


def slug(s, remove_whitespace=True, lowercase=True):
    """Condensed version of s, containing only lowercase alphanumeric characters."""
    res = ''.join((c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn'))
    if lowercase:
        res = res.lower()
    for c in string.punctuation:
        res = res.replace(c, '')
    res = re.sub('\s+', '' if remove_whitespace else ' ', res)
    res = res.encode('ascii', 'ignore').decode('ascii')
    assert re.match('[ A-Za-z0-9]*$', res)
    return res


def normalize_name(s):
    """Convert a string into a valid python attribute name.

    This function is called to convert ASCII strings to something that can pass as
    python attribute name, to be used with namedtuples.
    """
    s = s.replace('-', '_').replace('.', '_').replace(' ', '_')
    if s in keyword.kwlist:
        return s + '_'
    s = '_'.join(slug(ss, lowercase=False) for ss in s.split('_'))
    if not s:
        s = '_'
    if s[0] not in ascii_letters + '_':
        s = '_' + s
    return s


def encoded(string, encoding='utf8'):
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


class cached_property(object):

    """Decorator for read-only properties evaluated only once.

    It can be used to create a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached
            @cached_property()
            def randint(self):
                # will only be evaluated once.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is the last
    computed property value.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]

    inspired by the recipe by Christopher Arndt in the PythonDecoratorLibrary
    """

    def __call__(self, fget):
        self.fget = fget
        self.__doc__ = fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        if not hasattr(inst, '_cache'):
            inst._cache = {}
        if self.__name__ not in inst._cache:
            inst._cache[self.__name__] = self.fget(inst)
        return inst._cache[self.__name__]
