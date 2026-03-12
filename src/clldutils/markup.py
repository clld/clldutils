"""
Functionality for marking up text, mostly using Markdown.
"""
import io
import re
import csv
import sys
import enum
from typing import Union, Optional, Callable, Any, IO
import dataclasses
import urllib.parse
from collections.abc import Generator, Sequence, Iterable

from prettytable import PrettyTable, TableStyle
from markdown import markdown
from lxml import etree

from clldutils.misc import slug
from clldutils.text import replace_pattern

__all__ = [
    'Table', 'TableFormat',
    'iter_markdown_tables', 'iter_markdown_sections', 'add_markdown_text',
    'MarkdownLink', 'MarkdownImageLink']


class TableFormat(enum.Enum):
    """Available formatting options for tables."""
    pipe = enum.auto()  # pylint: disable=invalid-name
    simple = enum.auto()  # pylint: disable=invalid-name
    tsv = enum.auto()  # pylint: disable=invalid-name
    csv = enum.auto()  # pylint: disable=invalid-name
    ascii = enum.auto()  # pylint: disable=invalid-name

    @classmethod
    def get(cls, s: Union[None, str, 'TableFormat']):
        """Factory method, allowing selection of a format by name."""
        if s is None:
            return cls.pipe
        if isinstance(s, str):
            return getattr(cls, s)
        assert isinstance(s, cls), s
        return s


def _padded_row(row, num_rows: int, fill: str = '') -> list[Any]:
    row = list(row)
    while len(row) < num_rows:
        row.append(fill)
    return row


def _dedup_cols(ocols: Sequence[str]) -> list[str]:
    cols = []
    for col in ocols:
        i = 1
        while col in cols:
            i += 1
            col = f'{col}_{i}'
        cols.append(col)
    return cols


class Table(list):
    """
    A context manager to

    - aggregate rows in a table
    - which will be printed on exit.

    .. code-block:: python

        >>> with Table('col1', 'col2', tablefmt='simple') as t:
        ...     t.append(['v1', 'v2'])
        ...
         col1   col2
        ------ ------
         v1     v2

    For more control of the table rendering, a `Table` can be used without a `with` statement,
    calling :meth:`Table.render` instead:

    .. code-block:: python

        >>> t = Table('col1', 'col2')
        >>> t.extend([['z', 1], ['a', 2]])
        >>> print(t.render(sortkey=lambda r: r[0], tablefmt='simple'))
         col1   col2
        ------ ------
         a      2
         z      1
    """
    def __init__(
            self,
            *cols: str,
            rows: Optional[Sequence[Sequence[Any]]] = None,
            file: Optional[IO] = None,
            tablefmt: Optional[Union[str, TableFormat]] = None,
            floatfmt: Optional[str] = '.2',
    ):
        """

        """
        self.columns = list(cols)
        super().__init__(rows or [])
        self._file = file or sys.stdout
        self._tablefmt = TableFormat.get(tablefmt)
        self._floatfmt = floatfmt

    def render(  # pylint: disable=R0913,R0917
            self,
            sortkey: Callable[[Any], Any] = None,
            condensed: bool = True,
            verbose: bool = False,
            reverse: bool = False,
            tablefmt: Optional[Union[str, TableFormat]] = None,
            floatfmt: Optional[str] = None,
    ) -> str:
        """
        :param sortkey: A callable which can be used as key when sorting the rows.
        :param condensed: Flag signalling whether whitespace padding should be collapsed.
        :param verbose: Flag signalling whether to output additional info.
        :param reverse: Flag signalling whether we should sort in reverse order.
        :return: String representation of the table in the chosen format.
        """
        if not self.columns and not self:
            return ''

        tablefmt = self._tablefmt if tablefmt is None else TableFormat.get(tablefmt)

        if floatfmt is None:
            floatfmt = self._floatfmt

        if tablefmt in (TableFormat.tsv, TableFormat.csv):
            res = io.StringIO()
            w = csv.writer(res, delimiter='\t' if tablefmt == TableFormat.tsv else ',')
            w.writerow(self.columns)
            for row in (sorted(self, key=sortkey, reverse=reverse) if sortkey else self):
                w.writerow(row)
            res.seek(0)
            res = res.read()
            if res.endswith('\r\n'):
                res = res[:-2]
            return res

        table = PrettyTable()
        table.field_names = _dedup_cols(self.columns)
        rows = sorted(self, key=sortkey, reverse=reverse) if sortkey else self
        if self.columns:
            rows = [_padded_row(row, len(self.columns)) for row in rows]
        table.add_rows(rows)

        if tablefmt == TableFormat.pipe:
            table.set_style(TableStyle.MARKDOWN)
        elif tablefmt == TableFormat.simple:
            table.border = False
            table.preserve_internal_border = True
            table.align = 'l'
            table.vertical_char = ' '
            table.junction_char = ' '

        table.float_format = floatfmt
        res = str(table)

        if tablefmt == TableFormat.pipe:
            if condensed:
                # remove whitespace padding around column content:
                res = re.sub(r'\|[ ]+', '| ', res)
                res = re.sub(r'[ ]+\|', ' |', res)
            if verbose:
                res += f'\n\n({len(self)} rows)\n\n'
        return res

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(self.render(), file=self._file)


def iter_markdown_tables(text: str) -> Generator[tuple[list[str], list[list[str]]], None, None]:
    """
    Parse tables from a markdown formatted text.

    :param str text: markdown formatted text.
    :return: generator of (header, rows) pairs, where "header" is a `list` of column names and \
    rows is a list of lists of row values.
    """
    def split_row(line: str, outer_pipes: bool) -> list[str]:
        line = line.strip()
        if outer_pipes:
            assert line.startswith('|') and line.endswith('|'), 'inconsistent table formatting'
            line = line[1:-1].strip()
        return [c.strip() for c in line.split('|')]

    for header, rows, outer_pipes in _iter_table_blocks(text.splitlines()):
        yield split_row(header, outer_pipes), [split_row(row, outer_pipes) for row in rows]


def _iter_table_blocks(lines: Iterable[str]) -> Generator[tuple[str, list[str], bool], None, None]:
    # Tables are detected by
    # 1. A header line, i.e. a line with at least one `|`
    # 2. A line separating header and body of the form below
    sep = re.compile(r'\s*\|?\s*:?-(-)*:?\s*(\|\s*:?-(-)*:?\s*)+\|?\s*')

    lines = list(lines)
    header, table, outer_pipes = None, [], False
    for i, line in enumerate(lines):
        if header:
            if '|' not in line:
                if table:
                    yield header, table, outer_pipes
                header, table, outer_pipes = None, [], False
            else:
                if not sep.fullmatch(line):
                    table.append(line)
        else:
            if '|' in line and len(lines) > i + 1 and sep.fullmatch(lines[i + 1]):
                header = line
                outer_pipes = lines[i + 1].strip().startswith('|')
    if table:
        yield header, table, outer_pipes


def iter_markdown_sections(text) -> Generator[tuple[int, str, str], None, None]:
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
            if lines or header:
                yield level, header, ''.join(lines)
            lines, header, level = [], line, len(match.group('level'))
        else:
            lines.append(line)
    if lines or header:
        yield level, header, ''.join(lines)


def add_markdown_text(
        text: str,
        new: str,
        section: Optional[Union[Callable[[str], bool], str]] = None,
) -> str:
    """
    Append markdown text to a (specific section of a) markdown document.

    :param str text: markdown formatted text.
    :param str new: markdown formatted text to be inserted into `text`.
    :param section: optionally specifies a section to which to append `new`. `section` can either \
    be a `str` and then specifies the first section with a header containing `section` as \
    substring; or a callable and then specifies the first section for which `section` returns \
    a truthy value when passed the section header. \
    If `None`, `new` will be appended at the end.
    :return: markdown formatted text resulting from inserting `new` in `text`.
    :raises ValueError: The specified section was not encountered.
    """
    res = []
    for _, header, content in iter_markdown_sections(text):
        if header:
            res.append(header)
        res.append(content)
        if header and section and new:
            if (callable(section) and section(header)) or (section in header):
                res.append(new + '\n\n' if content.endswith('\n\n') else '\n\n' + new)
                new = None
    res = ''.join(res)
    if section is None:
        if res:
            res += '\n\n'
        res += new
    else:
        if new is not None:
            raise ValueError('Specified section not found')
    return res


@dataclasses.dataclass
class MarkdownLink:
    """
    Functionality to detect and manipulate links in markdown text.

    .. note::

        Link detection is limited to links with no nested square brackets in the label and
        no nested round brackets in the url. See :meth:`MarkdownLink.replace` for further
        limitations.

    Usage:

    .. code-block:: python

        >>> MarkdownLink.replace('[](http://example.com)', lambda ml: ml.update_url(scheme='https'))
        '[l](https://example.com)'
    """
    label: str
    url: str
    pattern: re.Pattern = re.compile(r'(?<!!)\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')
    html_link: tuple[str, str] = ('a', 'href')

    @classmethod
    def from_string(cls, s) -> 'MarkdownLink':
        """Create an instance from a Markdown formatted string, i.e. [...](...)."""
        try:
            return cls.from_match(cls.pattern.search(s))
        except AttributeError as e:
            raise ValueError('No markdown link found') from e

    @classmethod
    def from_match(cls, match) -> 'MarkdownLink':
        """Create an instance from a match object as returned e.g. by .pattern.search."""
        return cls(**match.groupdict())

    @property
    def parsed_url(self) -> urllib.parse.ParseResult:
        """Parsed components of the link's HREF value."""
        return urllib.parse.urlparse(self.url)

    @property
    def parsed_url_query(self) -> dict[str, list[str]]:
        """The query of the link's HREF value."""
        return urllib.parse.parse_qs(self.parsed_url.query, keep_blank_values=True)

    def update_url(self, **comps) -> 'MarkdownLink':
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
        return f'[{self.label}]({self.url})'

    @classmethod
    def replace(
            cls,
            md: str,
            repl: Callable[['MarkdownLink'], Any],
            simple: bool = True,
            markdown_kw: Optional[dict] = None,
    ) -> str:
        """
        Replace links in a markdown document.

        :param md: Markdown text.
        :param repl: A callable accepting a `MarkdownLink` instance as sole argument. Its return \
        value is passed to `str` to create the replacement content for the link.
        :param simple: Flag signaling whether to use simplistic link detection or not.
        :param markdown_kw: `dict` of keyword arguments to be used with `markdown.markdown` to \
        fine-tune link detection.
        :return: Updated markdown text

        .. note::

            The default link detection is rather simplistic and does **not** ignore markdown links
            in code blocks, etc. To force more accurate (but computationally expensive) link
            detection, pass `simple=False` when calling this method (and possibly use `markdown_kw`)
            to make link detection aware of particular options of the markdown implementation you
            want to use the output with. See
            `<https://python-markdown.github.io/reference/#markdown>`_ for details.

            .. code-block:: python

                >>> from clldutils.markup import MarkdownLink
                >>> md = '''abc
                ...
                ...     [label](url)
                ...
                ... def'''
                >>> print(MarkdownLink.replace(md, lambda ml: ml.update_url(path='xyz')))
                abc

                    [label](xyz)

                def
                >>> print(MarkdownLink.replace(
                ...     md, lambda ml: ml.update_url(path='xyz'), simple=False))
                abc

                    [label](url)

                def
                >>> md = '''abc
                ... ~~~
                ... [label](url)
                ... ~~~
                ... def'''
                >>> print(MarkdownLink.replace(
                ...     md, lambda ml: ml.update_url(path='xyz'), simple=False))
                abc
                ~~~
                [label](xyz)
                ~~~
                def
                >>> print(MarkdownLink.replace(
                ...     md,
                ...     lambda ml: ml.update_url(path='xyz'),
                ...     simple=False,
                ...     markdown_kw=dict(extensions=['fenced_code'])))
                abc
                ~~~
                [label](url)
                ~~~
                def

            **Limitations:** "Real" links are detected by running `markdown.markdown` and extracting
            a stack of links from the resulting HTML tags. Then "candidate" links are matched
            against these links in order. Thus, if the same link appears in a code block first and
            in regular text after, we will get it wrong:

            .. code-block:: python

                >>> md = '''abc
                ...
                ...     [label](url)
                ...
                ... [label](url)'''
                >>> print(MarkdownLink.replace(
                ...     md, lambda ml: ml.update_url(path='xyz'), simple=False))
                abc

                    [label](xyz)

                [label](url)
        """
        links = []
        if not simple:
            # We convert the markdown text to HTML and extract the links:
            tree = etree.parse(io.StringIO(markdown(md, **markdown_kw or {})), etree.HTMLParser())
            tag, attrib = cls.html_link
            for node in tree.xpath('.//' + tag):
                links.append((slug(''.join(node.itertext())), node.get(attrib)))
            links = list(reversed(links))

        def repl_wrapper(m: re.Match) -> Generator[str, None, None]:
            if not simple:
                if not links:
                    # We got them all.
                    yield m.string[m.start():m.end()]
                    return
                # See which link is next.
                label, url = links[-1]
                # Does the current link candidate match what is expected?
                if (label and (slug(m.group('label')) not in label)) or m.group('url') != url:
                    yield m.string[m.start():m.end()]
                    return
                links.pop()
            replacement = repl(cls.from_match(m))
            if replacement is not None:
                yield str(replacement)
            else:
                yield m.string[m.start():m.end()]

        return replace_pattern(cls.pattern, repl_wrapper, md)


@dataclasses.dataclass
class MarkdownImageLink(MarkdownLink):
    """Image links have a slightly different pattern."""
    pattern: re.Pattern = re.compile(r'!\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')
    html_link: tuple[str, str] = ('img', 'src')

    def __str__(self):
        return f'![{self.label}]({self.url})'
