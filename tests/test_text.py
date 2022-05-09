import re
import warnings

from clldutils import text


def test_replace_pattern():
    def repl(m):
        for _ in range(int(m.string[m.start():m.end()])):
            yield 'a'
    assert text.replace_pattern('^[0-9]+', repl, 'x3y\n2z', flags=re.M) == 'x3y\naaz'


def test_truncate_with_ellipsis(recwarn):
    warnings.simplefilter("always")
    assert text.truncate_with_ellipsis(' '.join(30 * ['a']), ellipsis='.').endswith('.')
    assert text.truncate_with_ellipsis(
        ' '.join(30 * ['a']), ellipsis='.', width=100).endswith('a')

    assert recwarn.pop(DeprecationWarning)
    warnings.simplefilter("default")


def test_strip_brackets():
    strings = ['arm((h)an[d])', '(hand)arm', 'a(hand)r(hand)m(hand)', 'arm⁽hand⁾']
    for string in strings:
        assert text.strip_brackets(string) == 'arm'
    assert text.strip_brackets('arm<hand>', brackets={"<": ">"}) == 'arm'


def test_split_text_with_context():
    assert text.split_text_with_context(' a b( )') == ['a', 'b( )']
    assert text.split_text_with_context("'a, b','c, d'", brackets={"'": "'"}, separators=",") == [
        "'a, b'", "'c, d'"]


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
