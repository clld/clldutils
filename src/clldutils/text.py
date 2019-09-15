import re
import textwrap

from clldutils.misc import nfilter, deprecated

# Brackets are pairs of single characters (<start-token>, <end-token>):
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
# To make it possible to detect compiled regex patterns, we store their type.
# See also http://stackoverflow.com/a/6102100
PATTERN_TYPE = type(re.compile('a'))
# A string of all unicode characters regarded as whitespace (by python's re module \s):
# See also http://stackoverflow.com/a/37903645
WHITESPACE = \
    '\t\n\x0b\x0c\r\x1c\x1d\x1e\x1f \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005' \
    '\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000'


class TextType(object):

    text = 1  # token outside of brackets
    open = 2  # start-token of a bracket
    context = 3  # non-bracket token inside brackets
    close = 4  # end-token of a bracket


def _tokens(text, brackets=None):
    if brackets is None:
        brackets = BRACKETS
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


def split_text_with_context(text, separators=WHITESPACE, brackets=None):
    """Splits text at separators outside of brackets.

    :param text:
    :param separators: An iterable of single character tokens.
    :param brackets:
    :return: A `list` of non-empty chunks.

    .. note:: This function leaves content in brackets in the chunks.
    """
    res, chunk = [], []
    for c, type_ in _tokens(text, brackets=brackets):
        if type_ == TextType.text and c in separators:
            res.append(''.join(chunk).strip())
            chunk = []
        else:
            chunk.append(c)
    res.append(''.join(chunk).strip())
    return nfilter(res)


def split_text(text, separators=re.compile('\s'), brackets=None, strip=False):
    """Split text along the separators unless they appear within brackets.

    :param separators: An iterable single characters or a compiled regex pattern.
    :param brackets: `dict` mapping start tokens to end tokens of what is to be \
    recognized as brackets.

    .. note:: This function will also strip content within brackets.
    """
    if not isinstance(separators, PATTERN_TYPE):
        separators = re.compile(
            '[{0}]'.format(''.join('\{0}'.format(c) for c in separators)))

    return nfilter(
        s.strip() if strip else s for s in
        separators.split(strip_brackets(text, brackets=brackets)))


def strip_chars(chars, sequence):
    """Strip the specified chars from anywhere in the text.

    :param chars: An iterable of single character tokens to be stripped out.
    :param sequence: An iterable of single character tokens.
    :return: Text string concatenating all tokens in sequence which were not stripped.
    """
    return ''.join(s for s in sequence if s not in chars)


def truncate_with_ellipsis(t, ellipsis='\u2026', width=40, **kw):
    deprecated('Use of deprecated function truncate_with_ellipsis! Use textwrap.shorten instead.')
    return textwrap.shorten(t, placeholder=ellipsis, width=width, **kw)
