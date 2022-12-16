"""
Support for common text manipulation tasks like stripping content in braces, etc.
"""
import re
import typing
import textwrap

from clldutils.misc import nfilter, deprecated

__all__ = [
    'strip_brackets', 'split_text_with_context', 'split_text', 'strip_chars', 'replace_pattern',
    'BRACKETS', 'WHITESPACE']

#: Brackets are pairs of single characters (<start-token>, <end-token>):
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
#: A string of all unicode characters regarded as whitespace (by python's re module \s):
#: See also http://stackoverflow.com/a/37903645
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
        if stack and c == stack[-1]:
            stack.pop()
            yield c, TextType.close
        elif c in brackets:
            stack.append(brackets[c])
            yield c, TextType.open
        elif not stack:
            yield c, TextType.text
        else:
            yield c, TextType.context


def strip_brackets(
        text: str,
        brackets: typing.Optional[dict] = None,
        strip_surrounding_whitespace: bool = True) -> str:
    """
    Strip brackets and what is inside brackets from text.

    .. code-block:: python

        >>> from clldutils.text import strip_brackets
        >>> strip_brackets('outside <inside> (outside)', brackets={'<': '>'})
        'outside  (outside)'

    .. note::

        If the text contains only one opening bracket, the rest of the text
        will be ignored. This is a feature, not a bug, as we want to avoid that
        this function raises errors too easily.
    """
    res = []
    for c, type_ in _tokens(text, brackets=brackets):
        if type_ == TextType.text:
            res.append(c)
    return ''.join(res).strip() if strip_surrounding_whitespace else ''.join(res)


def split_text_with_context(
        text: str,
        separators: str = WHITESPACE,
        brackets: typing.Optional[dict] = None) -> typing.List[str]:
    """
    Splits text at separators outside of brackets.

    :param text:
    :param separators: An iterable of single character tokens.
    :param brackets:
    :return: A `list` of non-empty chunks.

    .. code-block:: python

        >>> from clldutils.text import split_text_with_context
        >>> split_text_with_context('split-me (but-not-me)', separators='-')
        ['split', 'me (but-not-me)']

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


def split_text(
        text: str,
        separators: typing.Union[typing.Iterable, PATTERN_TYPE] = re.compile(r'\s'),
        brackets: typing.Optional[dict] = None,
        strip: bool = False) -> typing.List[str]:
    """
    Split text along the separators unless they appear within brackets.

    :param separators: An iterable of single characters or a compiled regex pattern.
    :param brackets: `dict` mapping start tokens to end tokens of what is to be \
    recognized as brackets.

    .. code-block:: python

        >>> from clldutils.text import split_text
        >>> split_text('split-me (but-not-me)', separators='-')
        ['split', 'me']

    .. note:: This function will also strip content within brackets.
    """
    if not isinstance(separators, PATTERN_TYPE):
        separators = re.compile(
            r'[{0}]'.format(''.join(r'\{0}'.format(c) for c in separators)))

    return nfilter(
        s.strip() if strip else s for s in
        separators.split(strip_brackets(text, brackets=brackets)))


def strip_chars(chars: typing.Iterable, sequence: typing.Iterable) -> str:
    """
    Strip the specified chars from anywhere in the text.

    :param chars: An iterable of single character tokens to be stripped out.
    :param sequence: An iterable of single character tokens.
    :return: Text string concatenating all tokens in sequence which were not stripped.
    """
    return ''.join(s for s in sequence if s not in chars)


def truncate_with_ellipsis(t, ellipsis='\u2026', width=40, **kw):
    deprecated('Use of deprecated function truncate_with_ellipsis! Use textwrap.shorten instead.')
    return textwrap.shorten(t, placeholder=ellipsis, width=width, **kw)


def replace_pattern(
        pattern: typing.Union[str, re.Pattern],
        repl: typing.Callable[[re.Match], typing.Generator[str, None, None]],
        text: str,
        flags=0) -> str:
    """
    Pretty much `re.sub`, but replacement functions are expected to be generators of strings.

    :param pattern: Compiled regex pattern or regex specified by `str`.
    :param repl: callable accepting a match instance as sole argument, yielding `str` as \
    replacements for the match.
    :param text: `str` in which to replace the pattern.
    :param flags: Flags suitable for passing to `re.compile` in case `pattern` is a `str`.
    :return: Text string with `pattern` replaced as implemented by `repl`.

    .. code-block:: python

        >>> from clldutils.text import replace_pattern
        >>> def multiply(m):
        ...     for i in range(int(m.string[m.start():m.end()])):
        ...         yield 'x'
        ...
        >>> replace_pattern('[0-9]+', multiply, 'a1b2c3')
        'axbxxcxxx'
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=flags)
    t, pos = [], 0
    for m in pattern.finditer(text):
        t.append(text[pos:m.start()])
        for chunk in repl(m):
            t.append(chunk)
        pos = m.end()
    t.append(text[pos:])
    return ''.join(t)
