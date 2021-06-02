"""
From zzzeek's "The Enum Recipe".

.. seealso:: `<http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/>`_
"""

import functools


@functools.total_ordering
class EnumSymbol(object):
    """Define a fixed symbol tied to a parent class."""

    def __init__(self, cls_, name, value, description, *args):
        self.cls_ = cls_
        self.name = name
        self.value = value
        self.description = description
        self.args = args

    def __reduce__(self):
        """Allow unpickling to return the symbol linked to the DeclEnum class."""
        return getattr, (self.cls_, self.name)  # pragma: no cover

    def __iter__(self):
        return iter([self.value, self.description])

    def __repr__(self):
        return "<%s>" % self.name

    def __hash__(self):
        return self.value

    def __str__(self):
        return '{0}'.format(self.value)

    def __lt__(self, other):
        return self.value < getattr(other, 'value', None)

    def __json__(self, *args, **kw):
        return self.value


class EnumMeta(type):
    """Generate new DeclEnum classes."""

    def __init__(cls, classname, bases, dict_):
        cls._reg = reg = cls._reg.copy()
        for k, v in dict_.items():
            if isinstance(v, tuple):
                sym = reg[v[0]] = EnumSymbol(cls, k, *v)
                setattr(cls, k, sym)
        super(EnumMeta, cls).__init__(classname, bases, dict_)

    def __iter__(cls):
        return iter(sorted(cls._reg.values()))


class DeclEnum(metaclass=EnumMeta):
    """Declarative enumeration."""

    _reg = {}

    @classmethod
    def from_string(cls, value):
        try:
            return cls._reg[value]
        except KeyError:
            raise ValueError("Invalid value for %r: %r" % (cls.__name__, value))

    @classmethod
    def get(cls, item):
        if item in iter(cls):
            return item
        for li in cls:
            if li.name == item or li.value == item:
                return li
        raise ValueError(item)

    @classmethod
    def values(cls):
        return list(cls._reg)
