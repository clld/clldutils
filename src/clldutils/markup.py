import re
import sys

from tabulate import tabulate

__all__ = ['Table', 'iter_markdown_tables']


class Table(list):

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


def iter_markdown_tables(text):
    """
    Parse tables from a markdown formatted text.

    :param text: `str` of markdown formatted text.
    :return: generator of (header, rows) pairs, where "header" is a `list` of column names and \
    rows is a `list` of `list`s of row values.
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
