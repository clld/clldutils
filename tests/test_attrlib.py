import re
import warnings

import pytest
import attr

from clldutils.attrlib import asdict, valid_enum_member, valid_re, valid_range, cmp_off


def test_cmp_off(recwarn):
    warnings.simplefilter("always")

    @attr.s(**cmp_off)
    class A:
        pass

    _ = A()
    assert not len(recwarn)


def test_asdict():
    class A(object):
        def asdict(self, **kw):
            return 'x'

    @attr.s
    class C(object):
        _b = attr.ib()
        a = attr.ib(default=attr.Factory(lambda: 5))

    assert asdict(C(A())) == {}
    assert asdict(C(A()), omit_private=False) == {'_b': 'x'}
    assert asdict(C(4), omit_defaults=False) == {'a': 5}


def test_valid_range():
    @attr.s
    class C(object):
        a = attr.ib(validator=valid_range(-1, 5))

    assert C(0).a == 0
    with pytest.raises(ValueError):
        C(-3)

    @attr.s
    class C(object):
        a = attr.ib(validator=valid_range(0, None))

    assert C(2).a == 2
    with pytest.raises(ValueError):
        C(-1)


def test_valid_re(recwarn):
    @attr.s
    class C(object):
        a = attr.ib(validator=valid_re('(a[0-9]+)?$'))

    assert recwarn.pop(DeprecationWarning)
    assert C('a1').a == 'a1'
    assert C('').a == ''

    with pytest.raises(ValueError):
        C('b')

    @attr.s
    class C(object):
        a = attr.ib(validator=valid_re(re.compile('a[0-9]+'), nullable=True))

    assert recwarn.pop(DeprecationWarning)
    assert C(None).a is None

    with pytest.raises(ValueError):
        C('b')


def test_valid_enum_member(recwarn):
    @attr.s
    class C(object):
        a = attr.ib(validator=valid_enum_member([1, 2, 3]))

    assert C(3).a == 3

    with pytest.raises(ValueError):
        C(5)
    assert recwarn.pop(DeprecationWarning)
