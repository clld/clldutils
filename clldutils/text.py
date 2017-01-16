# coding: utf8
from __future__ import unicode_literals, print_function, division
import re

def strip_brackets(text, brackets=None):
    """Strip brackets and what is inside brackets from text.
    
    .. bite:: If the text contains only one opening bracket, the rest of the text
      will be ignored. This is a feature, not a bug, as we want to avoid that
      this function raises errors too easily.
    """
    brackets = brackets or {
            "(": ")", "{": "}", "[": "]", "（": "）", "【": "】", "『": "』",
            "«": "»", "⁽": "⁾", "₍": "₎"}
    stack = []
    tmp_sequence = list(text)
    new_sequence = ''
    while tmp_sequence:
        itm = tmp_sequence.pop(0)
        if itm in brackets:
            stack += [brackets[itm]]
        if not stack:
            new_sequence += itm
        if itm in stack:
            stack.pop(stack.index(itm))
    return new_sequence

def split_text(text, separators="/,;~"):
    """Split text along the separators."""
    return re.split(r'\s*['+separators+']+\s*', text)

def strip_chars(chars, sequence):
    """Strip the specified chars from anywhere in the text."""
    return ''.join([s for s in sequence if s not in chars])
