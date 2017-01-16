# coding: utf8
from __future__ import unicode_literals, print_function, division
from clldutils.text import *

def test_strip_brackets():
    strings = ['arm(hand)', '(hand)arm', 'a(hand)r(hand)m(hand)', 'arm⁽hand⁾']
    for string in strings:
        assert strip_brackets(string) == 'arm'
    assert strip_brackets('arm<hand>', brackets={"<": ">"}) == 'arm'

def test_split_text():
    assert split_text('arm/hand')[1] == 'hand'
    assert split_text('arm,hand;foot')[2] == 'foot'
    assert split_text('arm/,;hand')[0] == 'arm'
    assert split_text('arm/,;hand')[1] == 'hand'
    assert split_text('arm/')[0] == 'arm'

def test_strip_chars():
    assert strip_chars('b', 'abcabc') == 'acac'
