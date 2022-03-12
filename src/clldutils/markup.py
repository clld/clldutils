import re
import sys
import typing
import urllib.parse

import attr
from tabulate import tabulate

__all__ = [
    'Table', 'iter_markdown_tables', 'iter_markdown_sections', 'MarkdownLink', 'MarkdownImageLink']


class Table(list):
    """
    A context manager to

    - aggregate rows in a table
    - which will be printed on exit.
    """
    def __init__(self, *cols, **kw):
        self.columns = list(cols)
        super(Table, self).__init__(kw.pop('rows', []))
        self._file = kw.pop('file', sys.stdout)
        self._kw = kw

    def render(self, sortkey=None, condensed=True, verbose=False, reverse=False, **kw):
        """

        :param sortkey: A callable which can be used as key when sorting the rows.
        :param condensed: Flag signalling whether whitespace padding should be collapsed.
        :param verbose: Flag signalling whether to output additional info.
        :param reverse: Flag signalling whether we should sort in reverse order.
        :param kw: Additional keyword arguments are passed to the `tabulate` function.
        :return: String representation of the table in the chosen format.
        """
        tab_kw = dict(tablefmt='pipe', headers=self.columns, floatfmt='.2f')
        tab_kw.update(self._kw)
        tab_kw.update(kw)
        res = tabulate(
            sorted(self, key=sortkey, reverse=reverse) if sortkey else self, **tab_kw)
        if tab_kw['tablefmt'] == 'pipe':
            if condensed:
                # remove whitespace padding around column content:
                res = re.sub(r'\|[ ]+', '| ', res)
                res = re.sub(r'[ ]+\|', ' |', res)
            if verbose:
                res += '\n\n(%s rows)\n\n' % len(self)
        return res

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(self.render(), file=self._file)


def iter_markdown_tables(text) -> \
        typing.Generator[typing.Tuple[typing.List[str], typing.List[typing.List[str]]], None, None]:
    """
    Parse tables from a markdown formatted text.

    :param str text: markdown formatted text.
    :return: generator of (header, rows) pairs, where "header" is a `list` of column names and \
    rows is a list of lists of row values.
    """
    def split_row(line, outer_pipes):
        line = line.strip()
        if outer_pipes:
            assert line.startswith('|') and line.endswith('|'), 'inconsistent table formatting'
            line = line[1:-1].strip()
        return [c.strip() for c in line.split('|')]

    for header, rows, outer_pipes in _iter_table_blocks(text.splitlines()):
        yield split_row(header, outer_pipes), [split_row(row, outer_pipes) for row in rows]


def _iter_table_blocks(lines):
    # Tables are detected by
    # 1. A header line, i.e. a line with at least one `|`
    # 2. A line separating header and body of the form below
    SEP = re.compile(r'\s*\|?\s*:?--(-)+:?\s*(\|\s*:?--(-)+:?\s*)+\|?\s*')

    lines = list(lines)
    header, table, outer_pipes = None, [], False
    for i, line in enumerate(lines):
        if header:
            if '|' not in line:
                if table:
                    yield header, table, outer_pipes
                header, table, outer_pipes = None, [], False
            else:
                if not SEP.fullmatch(line):
                    table.append(line)
        else:
            if '|' in line and len(lines) > i + 1 and SEP.fullmatch(lines[i + 1]):
                header = line
                outer_pipes = lines[i + 1].strip().startswith('|')
    if table:
        yield header, table, outer_pipes


def iter_markdown_sections(text) -> typing.Generator[typing.Tuple[int, str, str], None, None]:
    """
    Parse sections from a markdown formatted text.

    .. note:: We only recognize the "#" syntax for marking section headings.

    :param str text: markdown formatted text.
    :return: generator of (level, header, content) pairs, where "level" is an `int`, \
    "header" is the exact section heading (including "#"s and newline) or `None` and \
    "content" the markdown text of the section.
    """
    section_pattern = re.compile(r'(?P<level>[#]+)')
    lines, header, level = [], None, None
    for line in text.splitlines(keepends=True):
        match = section_pattern.match(line)
        if match:
            if lines:
                yield level, header, ''.join(lines)
            lines, header, level = [], line, len(match.group('level'))
        else:
            lines.append(line)
    if lines or header:
        yield level, header, ''.join(lines)


@attr.s
class MarkdownLink:
    """
    Functionality to detect and manipulate links in markdown text.

    >>> MarkdownLink.replace('[l](http://example.com)', lambda ml: ml.update_url(scheme='https'))
    '[l](https://example.com)'
    """
    label = attr.ib()
    url = attr.ib()
    pattern = re.compile(r'(^|[^!])\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')

    @classmethod
    def from_string(cls, s):
        try:
            return cls.from_match(cls.pattern.search(s))
        except AttributeError:
            raise ValueError('No markdown link found')

    @classmethod
    def from_match(cls, match):
        return cls(**match.groupdict())

    @property
    def parsed_url(self):
        return urllib.parse.urlparse(self.url)

    @property
    def parsed_url_query(self):
        return urllib.parse.parse_qs(self.parsed_url.query, keep_blank_values=True)

    def update_url(self, **comps):
        """
        Updates the `MarkdownLink.url` according to `comps`.

        :param comps: Recognized keywords are the names of the components of a named tuple \
        as returned by `urllib.parse.urlparse`. Values should be `str` or `dict` for the \
        keyword `query`.
        :return: Updated `MarkdownLink` instance.
        """
        old = self.parsed_url
        if ('query' in comps) and not isinstance(comps['query'], str):
            comps['query'] = urllib.parse.urlencode(comps['query'])
        parts = [
            comps.get(n, getattr(old, n))
            for n in 'scheme netloc path params query fragment'.split()]
        self.url = urllib.parse.urlunparse(parts)
        return self

    def __str__(self):
        return '[{0.label}]({0.url})'.format(self)

    @classmethod
    def replace(cls, md: str, repl: typing.Callable) -> str:
        """
        :param md: Markdown text.
        :param repl: A callable accepting a `MarkdownLink` instance as sole argument. Its return \
        value is passed to `str` to create the replacement content for the link.
        :return: Updated markdown text
        """
        current = 0
        res = []
        for m in cls.pattern.finditer(md):
            res.append(md[current:m.start()])
            current = m.end()
            replacement = repl(cls.from_match(m))
            if replacement is not None:
                res.append(str(replacement))
            else:
                res.append(md[m.start():m.end()])
        res.append(md[current:])
        return ''.join(res)


@attr.s
class MarkdownImageLink(MarkdownLink):
    pattern = re.compile(r'!\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')

    def __str__(self):
        return '![{0.label}]({0.url})'.format(self)
