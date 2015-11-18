# coding: utf8
from __future__ import unicode_literals
import random

from six import binary_type


def test_nfilter():
    from clldutils.misc import nfilter

    assert nfilter(range(5)) == list(range(1, 5))


def test_encoded():
    from clldutils.misc import encoded

    s = '\xe4'
    latin1 = binary_type(s.encode('latin1'))
    utf8 = binary_type(s.encode('utf8'))
    assert encoded(s) == utf8
    assert encoded(s, 'latin1') == latin1
    assert encoded(utf8) == utf8
    assert encoded(latin1) == utf8
    assert encoded(latin1, 'latin1') == latin1


def test_dict_merged():
    from clldutils.misc import dict_merged

    assert dict_merged(None, a=1) == {'a': 1}
    assert dict_merged(None, a=1, _filter=lambda i: i != 1) == {}
    assert dict_merged(None, a=None) == {}


def test_cached_property():
    from clldutils.misc import cached_property

    class C(object):
        @cached_property()
        def attr(self):
            return random.randint(1, 100000)

    c = C()
    call1 = c.attr
    assert call1 == c.attr
    del c._cache['attr']
    assert call1 != c.attr


def test_NoDefault():
    from clldutils.misc import NO_DEFAULT

    def f(default=NO_DEFAULT):
        if default is NO_DEFAULT:
            return 0
        return default

    assert f() != f(default=None)
    assert repr(NO_DEFAULT)


def test_slug():
    from clldutils.misc import slug

    assert slug('A B. \xe4C') == 'abac'


def test_normalize_name():
    from clldutils.misc import normalize_name

    assert normalize_name('class') == 'class_'
    assert normalize_name('a-name') == 'a_name'
    assert normalize_name('a näme') == 'a_name'
    assert normalize_name('Name') == 'Name'
    assert normalize_name('') == '_'
    assert normalize_name('1') == '_1'


def test_format_size():
    from clldutils.misc import format_size

    for i in range(10):
        assert format_size(1000 ** i)


def test_xmlchars():
    from clldutils.misc import xmlchars

    assert xmlchars('äöü') == 'äöü'
    assert xmlchars('ä\x08') == 'ä'


def test_UnicodeMixin():
    from clldutils.misc import UnicodeMixin

    class Test(UnicodeMixin):
        def __unicode__(self):
            return 'äöü'

    assert Test().__str__()
