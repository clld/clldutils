# coding: utf8
"""Support for reading delimiter-separated value files.

This module contains unicode aware replacements for :func:`csv.reader`
and :func:`csv.writer`. It was stolen/extracted from the ``csvkit``
project to allow re-use when the whole ``csvkit`` package isn't
required.

The original implementations were largely copied from
`examples in the csv module documentation <http://docs.python.org/library/csv.html\
#examples>`_.

.. seealso:: http://en.wikipedia.org/wiki/Delimiter-separated_values
"""
from __future__ import unicode_literals, division, absolute_import, print_function
import codecs
import csv
from collections import namedtuple, OrderedDict
from tempfile import NamedTemporaryFile

from six import (
    string_types, text_type, PY3, PY2, Iterator, binary_type, BytesIO, StringIO,
)
import attr

from clldutils.path import Path, move
from clldutils.misc import normalize_name, to_binary, encoded, cached_property
from clldutils import attrlib


def fix_kw(kw):
    """We make sure format parameters have the correct type."""
    for name in 'delimiter quotechar escapechar'.split():
        c = kw.get(name)
        if c and PY2 and isinstance(c, text_type):
            kw[name] = to_binary(c)
    return kw


class UTF8Recoder(object):

    """Iterator that reads an encoded stream and reencodes the input to UTF-8."""

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')


class UnicodeWriter(object):

    """Write Unicode data to a csv file."""

    def __init__(self, f=None, dialect=None, **kw):
        self.f = f
        self.encoding = kw.pop('encoding', 'utf8')
        self._close = False
        if dialect:
            self.encoding = dialect.encoding
            self.kw = dialect.as_python_formatting_parameters()
            self.kw.update(kw)
        else:
            self.kw = kw
        self.kw = fix_kw(self.kw)
        self._close = False

    def __enter__(self):
        if isinstance(self.f, (string_types, Path)):
            if isinstance(self.f, Path):
                self.f = self.f.as_posix()

            if PY3:  # pragma: no cover
                self.f = open(self.f, 'wt', encoding=self.encoding, newline='')
            else:
                self.f = open(self.f, 'wb')
            self._close = True
        elif self.f is None:
            self.f = StringIO(newline='') if PY3 else BytesIO()

        self.writer = csv.writer(self.f, **self.kw)
        return self

    def read(self):
        if hasattr(self.f, 'seek'):
            self.f.seek(0)
        if hasattr(self.f, 'read'):
            res = self.f.read()
            if PY3:  # pragma: no cover
                res = res.encode('utf8')
            return res

    def __exit__(self, type, value, traceback):
        if self._close:
            self.f.close()

    def writerow(self, row):
        if not PY3:
            row = ['' if s is None else encoded('%s' % s, self.encoding) for s in row]
        self.writer.writerow(row)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class UnicodeReader(Iterator):

    """Read Unicode data from a csv file."""

    def __init__(self, f, dialect=None, **kw):
        self.f = f
        self.encoding = kw.pop('encoding', 'utf8')
        self.newline = kw.pop('lineterminator', None)
        self.dialect = dialect
        if self.dialect:
            self.encoding = self.dialect.encoding
            self.kw = dialect.as_python_formatting_parameters()
            self.kw.update(kw)
        else:
            self.kw = kw
        self.kw = fix_kw(self.kw)
        self._close = False

    def __enter__(self):
        if isinstance(self.f, (string_types, Path)):
            if isinstance(self.f, Path):
                self.f = self.f.as_posix()

            if PY3:  # pragma: no cover
                self.f = open(
                    self.f, mode='rt', encoding=self.encoding, newline=self.newline or '')
            else:
                self.f = open(self.f, mode='rU')
            self._close = True
        elif hasattr(self.f, 'read'):
            if PY2:
                self.f = UTF8Recoder(self.f, self.encoding)
        else:
            lines = []
            for line in self.f:
                if PY2 and isinstance(line, text_type):
                    line = line.encode(self.encoding)
                elif PY3 and isinstance(line, binary_type):  # pragma: no cover
                    line = line.decode(self.encoding)
                lines.append(line)
            self.f = lines
        self.reader = csv.reader(self.f, **self.kw)
        self.lineno = -1
        return self

    def _next_row(self):
        self.lineno += 1
        return [
            s if isinstance(s, text_type) else s.decode(self.encoding)
            for s in next(self.reader)]

    def __next__(self):
        row = self._next_row()
        if self.dialect:
            while (row and self.dialect.commentPrefix and
                   row[0].startswith(self.dialect.commentPrefix)) or \
                    ((not row or set(row) == {''}) and self.dialect.skipBlankRows) or \
                    (self.lineno < self.dialect.skipRows):
                row = self._next_row()
            row = [self.dialect.trimmer(s) for s in row][self.dialect.skipColumns:]
        return row

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close:
            self.f.close()

    def __iter__(self):
        return self


class UnicodeReaderWithLineNumber(UnicodeReader):
    def __next__(self):
        """
        :return: a pair (1-based line number in the input, row)
        """
        # Retrieve the row, thereby incrementing the line number:
        row = UnicodeReader.__next__(self)
        return self.lineno + 1, row


class UnicodeDictReader(UnicodeReader):

    """Read Unicode data represented as one (ordered) dictionary per row."""

    def __init__(self, f, fieldnames=None, restkey=None, restval=None, **kw):
        self._fieldnames = fieldnames   # list of keys for the dict
        self.restkey = restkey          # key to catch long rows
        self.restval = restval          # default value for short rows
        self.line_num = 0
        UnicodeReader.__init__(self, f, **kw)

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                self._fieldnames = UnicodeReader.__next__(self)
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames

    def __next__(self):
        if self.line_num == 0:
            # Used only for its side effect.
            self.fieldnames
        row = UnicodeReader.__next__(self)
        self.line_num = self.reader.line_num

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while row == []:
            row = UnicodeReader.__next__(self)
        return self.item(row)

    def item(self, row):
        d = OrderedDict()
        for k, v in zip(self.fieldnames, row):
            d[k] = v
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d


class NamedTupleReader(UnicodeDictReader):

    """Read namedtuple objects from a csv file."""

    def __init__(self, f, **kw):
        self._cls = None
        UnicodeDictReader.__init__(self, f, **kw)

    @property
    def cls(self):
        if self._cls is None:
            self._cls = namedtuple('Row', list(map(normalize_name, self.fieldnames)))
        return self._cls

    def item(self, row):
        d = UnicodeDictReader.item(self, row)
        for name in self.fieldnames:
            d.setdefault(name, None)
        return self.cls(
            **{normalize_name(k): v for k, v in d.items() if k in self.fieldnames})


def reader(lines_or_file, namedtuples=False, dicts=False, encoding='utf8', **kw):
    """Convenience factory function for csv reader.

    :param lines_or_file: Content to be read. Either a file handle, a file path or a list\
    of strings.
    :param namedtuples: Yield namedtuples.
    :param dicts: Yield dicts.
    :param encoding: Encoding of the content.
    :param kw: Keyword parameters are passed through to csv.reader.
    :return: A generator over the rows.
    """
    # Either namedtuples or dicts can be chosen as output format.
    assert not (namedtuples and dicts)

    if namedtuples:
        _reader = NamedTupleReader
    elif dicts:
        _reader = UnicodeDictReader
    else:
        _reader = UnicodeReader

    with _reader(lines_or_file, encoding=encoding, **fix_kw(kw)) as r:
        for item in r:
            yield item


def rewrite(fname, visitor, **kw):
    """Utility function to rewrite rows in tsv files.

    :param fname: Path of the dsv file to operate on.
    :param visitor: A callable that takes a line-number and a row as input and returns a \
    (modified) row or None to filter out the row.
    :param kw: Keyword parameters are passed through to csv.reader/csv.writer.
    """
    if not isinstance(fname, Path):
        assert isinstance(fname, string_types)
        fname = Path(fname)

    assert fname.is_file()
    with NamedTemporaryFile(delete=False) as fp:
        tmp = Path(fp.name)

    with UnicodeReader(fname, **kw) as reader_:
        with UnicodeWriter(tmp, **kw) as writer:
            for i, row in enumerate(reader_):
                row = visitor(i, row)
                if row is not None:
                    writer.writerow(row)
    move(tmp, fname)


def add_rows(fname, *rows):
    with NamedTemporaryFile(delete=False) as fp:
        tmp = Path(fp.name)

    with UnicodeWriter(tmp) as writer:
        if fname.exists():
            with UnicodeReader(fname) as reader_:
                for row in reader_:
                    writer.writerow(row)
        writer.writerows(rows)
    move(tmp, fname)


class DictFilter(object):
    def __init__(self, filter_):
        self.header = None
        self.filter = filter_
        self.removed = 0

    def __call__(self, i, row):
        if i == 0:
            self.header = row
            return row
        if row:
            item = dict(zip(self.header, row))
            if self.filter(item):
                return row
            else:
                self.removed += 1


def filter_rows_as_dict(fname, filter_, **kw):
    """
    Rewrite a dsv file, filtering the rows.

    :param fname: Path to dsv file
    :param filter_: callable which accepts a `dict` with a row's data as single argument\
    returning a `Boolean` indicating whether to keep the row (`True`) or to discard it \
    `False`.
    :param kw: Keyword arguments to be passed `UnicodeReader` and `UnicodeWriter`.
    :return: The number of rows that have been removed.
    """
    filter_ = DictFilter(filter_)
    rewrite(fname, filter_, **kw)
    return filter_.removed


def non_negative_int(*_):
    return attr.validators.and_(
        attr.validators.instance_of(int), attrlib.valid_range(0, None))


@attr.s
class Dialect(object):
    """
    A CSV dialect specification.

    .. seealso:: http://w3c.github.io/csvw/metadata/#dialect-descriptions
    """
    encoding = attr.ib(
        default="utf-8",
        validator=attr.validators.instance_of(text_type))
    lineTerminators = attr.ib(
        default=attr.Factory(lambda: ["\r\n", "\n"]))
    quoteChar = attr.ib(
        default='"',
    )
    doubleQuote = attr.ib(
        default=True,
        validator=attr.validators.instance_of(bool))
    skipRows = attr.ib(
        default=0,
        validator=non_negative_int)
    commentPrefix = attr.ib(
        default="#",
        validator=attr.validators.optional(attr.validators.instance_of(text_type)))
    header = attr.ib(
        default=True,
        validator=attr.validators.instance_of(bool))
    headerRowCount = attr.ib(
        default=1,
        validator=non_negative_int)
    delimiter = attr.ib(
        default=",",
        validator=attr.validators.instance_of(text_type))
    skipColumns = attr.ib(
        default=0,
        validator=non_negative_int)
    skipBlankRows = attr.ib(
        default=False,
        validator=attr.validators.instance_of(bool))
    skipInitialSpace = attr.ib(
        default=False,
        validator=attr.validators.instance_of(bool))
    trim = attr.ib(
        default='false',
        validator=attr.validators.in_(['true', 'false', 'start', 'end']),
        convert=lambda v: '{0}'.format(v).lower() if isinstance(v, bool) else v)

    def updated(self, **kw):
        res = Dialect(**attr.asdict(self))
        for k, v in kw.items():
            setattr(res, k, v)
        return res

    @cached_property()
    def escape_character(self):
        return None if self.quoteChar is None else ('"' if self.doubleQuote else '\\')

    @cached_property()
    def line_terminators(self):
        return [self.lineTerminators] \
            if isinstance(self.lineTerminators, text_type) else self.lineTerminators

    @cached_property()
    def trimmer(self):
        return {
            'true': lambda s: s.strip(),
            'false': lambda s: s,
            'start': lambda s: s.lstrip(),
            'end': lambda s: s.rstrip()
        }[self.trim]

    def asdict(self, omit_defaults=True):
        return attrlib.asdict(self, omit_defaults=omit_defaults)

    def as_python_formatting_parameters(self):
        return dict(
            delimiter=self.delimiter,
            doublequote=self.doubleQuote,
            # We have to hack around incompatible ways escape char is interpreted in csvw
            # and python's csv lib:
            escapechar=self.escape_character if self.escape_character is None else '\\',
            lineterminator=self.line_terminators[0],
            quotechar=self.quoteChar,
            skipinitialspace=self.skipInitialSpace,
            strict=True)
