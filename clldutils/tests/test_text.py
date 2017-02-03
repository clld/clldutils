# coding: utf8
from __future__ import unicode_literals, print_function, division
import re

from clldutils import text


def test_truncate_with_ellipsis():
    assert text.truncate_with_ellipsis(' '.join(30 * ['a']), ellipsis='.').endswith('.')
    assert text.truncate_with_ellipsis(
        ' '.join(30 * ['a']), ellipsis='.', width=100).endswith('a')


def test_strip_brackets():
    strings = ['arm((h)an[d])', '(hand)arm', 'a(hand)r(hand)m(hand)', 'arm⁽hand⁾']
    for string in strings:
        assert text.strip_brackets(string) == 'arm'
    assert text.strip_brackets('arm<hand>', brackets={"<": ">"}) == 'arm'


def test_split_text_with_context():
    assert text.split_text_with_context(' a b( )') == ['a', 'b( )']


def test_split_text():
    assert text.split_text('arm han( )d')[1] == 'hand'
    assert text.split_text('arm han( )d', brackets={})[1] == 'han('
    assert text.split_text('arm h[\t]and   foot')[2] == 'foot'
    assert text.split_text('arm \t\n hand')[1] == 'hand'
    assert text.split_text('arm ')[0] == 'arm'
    assert text.split_text('a(b)c d[e]f', brackets={'(': ')'}) == ['ac', 'd[e]f']
    assert text.split_text('a b c') == ['a', 'b', 'c']
    assert text.split_text('a/b/c', separators=re.compile('/b/')) == ['a', 'c']
    assert text.split_text('a/b/c', separators='/') == ['a', 'b', 'c']
    assert text.split_text('a , b\t; c;', separators=',;', strip=True) == ['a', 'b', 'c']


def test_strip_chars():
    assert text.strip_chars('b', 'abcabc') == 'acac'
