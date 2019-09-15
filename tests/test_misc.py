# coding: utf8
from __future__ import unicode_literals
import random
import itertools
import warnings

from six import binary_type

import pytest

from clldutils.misc import *


def test_log_or_raise(mocker):
    with pytest.raises(ValueError):
        log_or_raise('')

    log = mocker.Mock()
    log_or_raise('test', log=log)
    assert log.warn.called


def test_nfilter():
    assert nfilter(range(5)) == list(range(1, 5))


def test_encoded():
    s = '\xe4'
    latin1 = binary_type(s.encode('latin1'))
    utf8 = binary_type(s.encode('utf8'))
    assert encoded(s) == utf8
    assert encoded(s, 'latin1') == latin1
    assert encoded(utf8) == utf8
    assert encoded(latin1) == utf8
    assert encoded(latin1, 'latin1') == latin1


def test_dict_merged():
    assert dict_merged(None, a=1) == {'a': 1}
    assert dict_merged(None, a=1, _filter=lambda i: i != 1) == {}
    assert dict_merged(None, a=None) == {}


def test_lazyproperty():
    class C(object):
        @lazyproperty
        def attr(self, _ints=itertools.count()):
            return next(_ints)

    assert isinstance(C.attr, lazyproperty)
    c = C()
    call1 = c.attr
    assert call1 == c.attr
    del c.attr
    assert call1 != c.attr


def test_cached_property():
    with pytest.warns(DeprecationWarning):
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
    def f(default=NO_DEFAULT):
        if default is NO_DEFAULT:
            return 0
        return default

    assert f() != f(default=None)
    assert repr(NO_DEFAULT)


def test_slug():
    assert slug('A B. \xe4C') == 'abac'


def test_format_size():
    for i in range(10):
        assert format_size(1000 ** i)


def test_xmlchars():
    assert xmlchars('äöü') == 'äöü'
    assert xmlchars('ä\x08') == 'ä'


def test_UnicodeMixin(recwarn):
    class Test(UnicodeMixin):
        def __unicode__(self):
            return 'äöü'

    warnings.simplefilter("always")
    assert Test().__str__()
    assert recwarn.pop(DeprecationWarning)
    warnings.simplefilter("default")


def test_data_url_from_string():
    from clldutils.path import Path

    assert data_url('ü') == 'data:application/octet-stream;base64,w7w='
    assert data_url(Path(__file__)).startswith('data:')
    assert data_url(Path(__file__), mimetype='text/plain').startswith('data:text/plain')
