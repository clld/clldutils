# coding: utf8
from __future__ import unicode_literals, print_function, division


def test_find():
    from clldutils.licenses import find

    assert find('http://creativecommons.org/licenses/by/4.0').id == 'CC-BY-4.0'
    assert find('CC-BY-4.0').url == 'https://creativecommons.org/licenses/by/4.0/'
