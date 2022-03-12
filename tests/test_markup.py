import io
from operator import itemgetter

import pytest

from clldutils.markup import *


def test_Table():
    t = Table()
    assert t.render() == ''

    t = Table('a', 'b', rows=[[1, 2], [3, 4]])
    assert t.render() == \
        '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |'
    assert t.render(condensed=False) == \
        '|   a |   b |\n|----:|----:|\n|   1 |   2 |\n|   3 |   4 |'
    assert t.render(verbose=True) == \
        '| a | b |\n|----:|----:|\n| 1 | 2 |\n| 3 | 4 |\n\n(2 rows)\n\n'
    assert t.render(sortkey=itemgetter(1), reverse=True) == \
        '| a | b |\n|----:|----:|\n| 3 | 4 |\n| 1 | 2 |'


def test_Table_context(capsys):
    with Table('a', 'b', tablefmt='simple') as t:
        t.append([1, 2.345])
    out, _ = capsys.readouterr()
    assert out == '  a     b\n---  ----\n  1  2.35\n'

    f = io.StringIO()
    with Table('a', 'b', tablefmt='simple', file=f) as t:
        t.append([1, 2.345])
    assert f.getvalue() == '  a     b\n---  ----\n  1  2.35\n'


def test_iter_markdown_tables():
    header, rows = ['a', 'b'], [[1, 2], [3, 4]]
    text = Table(*header, **dict(rows=rows)).render() + '\nabcd'
    assert list(iter_markdown_tables(text))[0] == \
        (header, [[str(v) for v in r] for r in rows])
    assert list(iter_markdown_tables('a|b\n---|---\n1|2'))[0] == (header, [['1', '2']])


@pytest.mark.parametrize(
    'text',
    [
        'leading\n# title\n\n## sec1\nsec1 content\n\n## sec2\n\n',
        '\n# title\n\n## sec1\nsec1 content\n\n## sec2',
    ]
)
def test_iter_markdown_sections(text):
    res = []
    for _, header, content in iter_markdown_sections(text):
        res.extend(t for t in [header, content] if t is not None)
    assert ''.join(res) == text


def test_markdownlink():
    def repl(ml):
        ml.label = 'y'
        q = ml.parsed_url_query
        q.update(x=1)
        ml.update_url(query=q)
        return ml

    s = MarkdownLink.replace('stuff [label](http://example.com/p)', repl)
    ml = MarkdownLink.from_string(s)
    assert ml.parsed_url_query['x'] == ['1'] and ml.label == 'y'

    with pytest.raises(ValueError):
        MarkdownLink.from_string(str(MarkdownImageLink(label='x', url='y')))

    s = '[a](b)'
    assert MarkdownLink.replace(s, lambda m: None) == s
