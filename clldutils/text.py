# coding: utf8
from __future__ import unicode_literals, print_function, division
import textwrap

BRACKETS = {
    "(": ")",
    "{": "}",
    "[": "]",
    "（": "）",
    "【": "】",
    "『": "』",
    "«": "»",
    "⁽": "⁾",
    "₍": "₎"
}


class TextType(object):
    text = 1
    open = 2
    context = 3
    close = 4


def _tokens(text, brackets=None):
    brackets = brackets or BRACKETS
    stack = []
    for c in text:
        if c in brackets:
            stack.append(brackets[c])
            yield c, TextType.open
        elif stack and c == stack[-1]:
            stack.pop()
            yield c, TextType.close
        elif not stack:
            yield c, TextType.text
        else:
            yield c, TextType.context


def strip_brackets(text, brackets=None):
    """Strip brackets and what is inside brackets from text.

    .. note::
        If the text contains only one opening bracket, the rest of the text
        will be ignored. This is a feature, not a bug, as we want to avoid that
        this function raises errors too easily.
    """
    res = []
    for c, type_ in _tokens(text, brackets=brackets):
        if type_ == TextType.text:
            res.append(c)
    return ''.join(res).strip()


def iter_text(text, separators="/,;~", brackets=None):
    word = []

    for c, type_ in _tokens(text, brackets=brackets):
        if type_ == TextType.text:
            if c in separators:
                word = ''.join(word).strip()
                if word:
                    yield word
                word = []
            else:
                word.append(c)
    word = ''.join(word).strip()
    if word:
        yield word


def split_text(text, separators="/,;~", brackets=None):
    """
    Split text along the separators unless they appear within brackets.
    """
    return list(iter_text(text, separators=separators, brackets=brackets))


def strip_chars(chars, sequence):
    """Strip the specified chars from anywhere in the text."""
    return ''.join([s for s in sequence if s not in chars])


def truncate_with_ellipsis(t, ellipsis='\u2026', width=40, **kw):
    return t if len(t) <= width else textwrap.wrap(t, width=width, **kw)[0] + ellipsis
