# coding: utf8
"""
Functionality to read and write metadata for CSV files.

This module implements (partially) the W3C recommendation
"Metadata Vocabulary for Tabular Data".

.. seealso:: https://www.w3.org/TR/tabular-metadata/
"""
from __future__ import unicode_literals, print_function, division
import re
from collections import OrderedDict
from json import loads, dumps
import datetime
from decimal import Decimal
import base64
import binascii

from six import text_type
import attr
from uritemplate import URITemplate
from dateutil import parser
import isodate

from clldutils.dsv import Dialect, reader
from clldutils.jsonlib import load, dump
from clldutils.path import Path
from clldutils.misc import UnicodeMixin, cached_property, to_binary
from clldutils import attrlib

# Level 1 variable names according to https://tools.ietf.org/html/rfc6570#section-2.3:
_varchar = '([a-zA-Z0-9_]|\%[a-fA-F0-9]{2})'
_varname = re.compile('(' + _varchar + '([.]?' + _varchar + ')*)$')


def uri_template_property():
    """
    Note: We do not currently provide support for supplying the "_" variables like "_row"
    when expanding a URI template.

    .. seealso:: http://w3c.github.io/csvw/metadata/#uri-template-properties
    """
    return attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(URITemplate)),
        convert=lambda v: v if v is None else URITemplate(v))


class Link(UnicodeMixin):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#link-properties
    """
    def __init__(self, string):
        self.string = string

    def __unicode__(self):
        return self.string

    def asdict(self, omit_defaults=True):
        return self.string

    def resolve(self, base):
        if not base:
            return self.string
        if isinstance(base, Path):
            return base.joinpath(self.string)
        if not base.endswith('/'):
            base += '/'
        return base + self.string


class NaturalLanguage(UnicodeMixin, OrderedDict):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#natural-language-properties
    """
    def __init__(self, value):
        OrderedDict.__init__(self)
        self.value = value
        if isinstance(self.value, text_type):
            self[None] = [self.value]
        elif isinstance(self.value, (list, tuple)):
            self[None] = list(self.value)
        elif isinstance(self.value, (dict, OrderedDict)):
            for k, v in self.value.items():
                if not isinstance(v, (list, tuple)):
                    v = [v]
                self[k] = v
        else:
            raise ValueError('invalid value type for NaturalLanguage')

    def asdict(self, omit_defaults=True):
        if list(self.keys()) == [None]:
            if len(self[None]) == 1:
                return self.getfirst()
            return self[None]
        return OrderedDict(
            [('und' if k is None else k, v[0] if len(v) == 1 else v)
             for k, v in self.items()])

    def add(self, string, lang=None):
        if lang not in self:
            self[lang] = []
        self[lang].append(string)

    def __unicode__(self):
        return self.getfirst() or list(self.values())[0][0]

    def getfirst(self, lang=None):
        return self.get(lang, [None])[0]


@attr.s
class DescriptionBase(object):
    """
    Container for
    - common properties (see http://w3c.github.io/csvw/metadata/#common-properties)
    - @-properies.
    """
    common_props = attr.ib(default=attr.Factory(dict))
    at_props = attr.ib(default=attr.Factory(dict))

    @staticmethod
    def partition_properties(d):
        c, a, dd = {}, {}, {}
        for k, v in (d or {}).items():
            if k.startswith('@'):
                a[k[1:]] = v
            elif ':' in k:
                c[k] = v
            else:
                dd[k] = v
        return dict(common_props=c, at_props=a, **dd)

    @classmethod
    def fromvalue(cls, d):
        return cls(**cls.partition_properties(d))

    def _iter_dict_items(self, omit_defaults):
        def _asdict_single(v):
            return v.asdict(omit_defaults=omit_defaults) if hasattr(v, 'asdict') else v

        def _asdict_multiple(v):
            if isinstance(v, (list, tuple)):
                return [_asdict_single(vv) for vv in v]
            return _asdict_single(v)

        for k, v in sorted(self.at_props.items()):
            yield '@' + k, _asdict_multiple(v)

        for k, v in sorted(self.common_props.items()):
            yield k, _asdict_multiple(v)

        for k, v in attrlib.asdict(self, omit_defaults=omit_defaults).items():
            if k not in ['common_props', 'at_props']:
                yield k, _asdict_multiple(v)

    def asdict(self, omit_defaults=True):
        return OrderedDict(
            [(k, v) for k, v in
             self._iter_dict_items(omit_defaults) if v not in [None, [], {}]])


# -----------------------------------------------------------------------------
# Basic datatypes
#
# We model the hierarchy of basic datatypes using derived classes.
#
class anyAtomicType(UnicodeMixin):
    name = 'any'

    def __unicode__(self):
        return self.name or self.__class__.__name__

    @staticmethod
    def derived_description(datatype):
        return {}

    @staticmethod
    def to_python(v, **kw):
        return v  # pragma: no cover

    @staticmethod
    def to_string(v, **kw):
        return '{0}'.format(v)


class anyURI(anyAtomicType):
    name = 'anyURI'


class base64Binary(anyAtomicType):
    name = 'binary'

    @staticmethod
    def to_python(v, **kw):
        try:
            res = to_binary(v, encoding='ascii')
        except UnicodeEncodeError:
            raise ValueError()
        try:
            base64.decodestring(res)
        except Exception:
            raise ValueError('invalid base64 encoding')
        return res

    @staticmethod
    def to_string(v, **kw):
        return v.decode()


class hexBinary(anyAtomicType):
    name = 'hexBinary'

    @staticmethod
    def to_python(v, **kw):
        try:
            res = to_binary(v, encoding='ascii')
        except UnicodeEncodeError:
            raise ValueError()
        try:
            binascii.unhexlify(res)
        except TypeError:
            raise ValueError('invalid hexBinary encoding')
        return res

    @staticmethod
    def to_string(v, **kw):
        return v.decode()


class boolean(anyAtomicType):
    """
    http://w3c.github.io/csvw/syntax/#formats-for-booleans
    """
    name = 'boolean'

    @staticmethod
    def derived_description(datatype):
        if datatype.format:
            true, false = [[v] for v in datatype.format.split('|')]
        else:
            true, false = ['true', '1'], ['false', '0']
        return dict(true=true, false=false)

    @staticmethod
    def to_python(s, true=('true', '1'), false=('false', '0')):
        if isinstance(s, bool):
            return s
        if s in true:
            return True
        if s in false:
            return False
        raise ValueError('invalid lexical value for boolean: %s' % s)

    @staticmethod
    def to_string(v, true=('true', '1'), false=('false', '0')):
        return true[0] if v else false[0]


def dt_format_and_regex(fmt):
    """
    .. seealso:: http://w3c.github.io/csvw/syntax/#formats-for-dates-and-times
    """
    if fmt is None:
        return dict(fmt=None, tz_marker=None, regex=None)

    # First, we strip off an optional timezone marker:
    tz_marker = None
    match = re.search('(?P<marker> ?[xX]{1,3})$', fmt)
    if match:
        tz_marker = match.group('marker')
        if len(set(tz_marker.strip())) != 1:  # mixing x and X is not allowed!
            raise ValueError(fmt)
        fmt = fmt[:match.start()]

    date_patterns = {
        "yyyy-MM-dd",  # e.g., 2015-03-22
        "yyyyMMdd",  # e.g., 20150322
        "dd-MM-yyyy",  # e.g., 22-03-2015
        "d-M-yyyy",  # e.g., 22-3-2015
        "MM-dd-yyyy",  # e.g., 03-22-2015
        "M-d-yyyy",  # e.g., 3-22-2015
        "dd/MM/yyyy",  # e.g., 22/03/2015
        "d/M/yyyy",  # e.g., 22/3/2015
        "MM/dd/yyyy",  # e.g., 03/22/2015
        "M/d/yyyy",  # e.g., 3/22/2015
        "dd.MM.yyyy",  # e.g., 22.03.2015
        "d.M.yyyy",  # e.g., 22.3.2015
        "MM.dd.yyyy",  # e.g., 03.22.2015
        "M.d.yyyy",  # e.g., 3.22.2015
    }

    time_patterns = {"HH:mm:ss", "HHmmss", "HH:mm", "HHmm"}

    # We map dateTime component markers to corresponding fromat specs and regular
    # expressions used for formatting and parsing.
    translate = {
        'yyyy': ('{dt.year:04d}', '(?P<year>[0-9]{4})'),
        'MM': ('{dt.month:02d}', '(?P<month>[0-9]{2})'),
        'dd': ('{dt.day:02d}', '(?P<day>[0-9]{2})'),
        'M': ('{dt.month}', '(?P<month>[0-9]{1,2})'),
        'd': ('{dt.day}', '(?P<day>[0-9]{1,2})'),
        'HH': ('{dt.hour:02d}', '(?P<hour>[0-9]{2})'),
        'mm': ('{dt.minute:02d}', '(?P<minute>[0-9]{2})'),
        'ss': ('{dt.second:02d}', '(?P<second>[0-9]{2})'),
    }

    for dt_sep in ' T':  # Only a single space or "T" may separate date and time format.
        # Since space or "T" isn't allowed anywhere else in the format, checking whether
        # we are dealing with a date or dateTime format is simple:
        if dt_sep in fmt:
            break
    else:
        dt_sep = None

    msecs = None  # The maximal number of decimal places for fractions of seconds.
    if dt_sep:
        dfmt, tfmt = fmt.split(dt_sep)
        if '.' in tfmt:  # There is a microseconds marker.
            tfmt, msecs = tfmt.split('.')  # Strip it off ...
            if set(msecs) != {'S'}:  # ... make sure it's valid ...
                raise ValueError(fmt)
            msecs = len(msecs)   # ... and store it's length.
    else:
        dfmt, tfmt = fmt, None

    # Now we can check whether the bare date and time formats are valid:
    if dfmt not in date_patterns or (tfmt and tfmt not in time_patterns):
        raise ValueError(fmt)

    regex, format = '', ''  # Initialize the output.

    for d_sep in '.-/':  # Determine the separator used for date components.
        if d_sep in dfmt:
            break
    else:
        raise ValueError('invalid date separator')  # pragma: no cover

    # Iterate over date components, converting them to string format specs and regular
    # expressions.
    for i, part in enumerate(dfmt.split(d_sep)):
        if i > 0:
            format += d_sep
            regex += re.escape(d_sep)
        f, r = translate[part]
        format += f
        regex += r

    if dt_sep:
        format += dt_sep
        regex += re.escape(dt_sep)

        # For time components the only valid separator is ":".
        for i, part in enumerate(tfmt.split(':')):
            if i > 0:
                format += ':'
                regex += re.escape(':')
            f, r = translate[part]
            format += f
            regex += r

    # Fractions of seconds are a bit of a problem, because datetime objects only offer
    # microseconds.
    if msecs:
        format += '.{microsecond:.%s}' % msecs
        regex += '\.(?P<microsecond>[0-9]{1,%s})' % msecs

    return dict(regex=re.compile(regex), fmt=format, tz_marker=tz_marker)


class dateTime(anyAtomicType):
    name = 'datetime'

    @staticmethod
    def derived_description(datatype):
        return dt_format_and_regex(datatype.format)

    @staticmethod
    def to_python(v, regex=None, fmt=None, tz_marker=None):
        if regex is None:
            return parser.parse(v)
        try:
            comps = regex.match(v).groupdict()
        except AttributeError:
            raise ValueError()
        if 'microsecond' in comps:
            # We have to convert decimal fractions of seconds to microseconds.
            # This is done by first chopping off anything under 6 decimal places,
            # then (in case we got less precision) right-padding with 0 to get a
            # 6-digit number.
            comps['microsecond'] = comps['microsecond'][:6].ljust(6, '0')
        res = datetime.datetime(**{k: int(v) for k, v in comps.items()})
        if tz_marker:
            # Let dateutils take care of parsing the timezone info:
            res = res.replace(tzinfo=parser.parse(v).tzinfo)
        return res

    @staticmethod
    def to_string(v, regex=None, fmt=None, tz_marker=None):
        if fmt is None:
            return v.isoformat()
        res = fmt.format(dt=v, microsecond='{0:%f}'.format(v))
        if tz_marker:
            # We start out with the default timezone info: +##:##
            tz_offset = v.isoformat()[-6:]
            assert tz_offset[0] in '+-'
            tz_offset = tz_offset.split(':')
            if tz_marker.startswith(' '):
                res += ' '
            res += tz_offset[0]
            tz_type = len(tz_marker.strip())
            if tz_type == 3:
                res += ':'
            if (tz_type == 1 and tz_offset[1] != '00') or tz_type > 1:
                res += tz_offset[1]
        return res


class date(dateTime):
    name = 'date'

    @staticmethod
    def derived_description(datatype):
        return dt_format_and_regex(datatype.format or 'yyyy-MM-dd')

    @staticmethod
    def to_python(v, regex=None, fmt=None, tz_marker=None):
        return dateTime.to_python(v, regex=regex, fmt=fmt).date()


class dateTimeStamp(dateTime):
    name = 'dateTimeStamp'

    @staticmethod
    def derived_description(datatype):
        res = dt_format_and_regex(datatype.format or 'yyyy-MM-ddTHH:mm:ss.SSSSSSXXX')
        if not res['tz_marker']:
            raise ValueError('dateTimeStamp must have timezone marker')
        return res


class duration(anyAtomicType):
    name = 'duration'

    @staticmethod
    def derived_description(datatype):
        return dict(format=datatype.format)

    @staticmethod
    def to_python(v, format=None, **kw):
        if format and not re.match(format, v):
            raise ValueError()
        return isodate.parse_duration(v)

    @staticmethod
    def to_string(v, **kw):
        return isodate.duration_isoformat(v)


class decimal(anyAtomicType):
    name = 'decimal'

    # TODO:
    # - use babel.numbers.NumberPattern.apply to format a value!
    # - use babel.numbers.parse_number to parse a value!
    @staticmethod
    def derived_description(datatype):
        if datatype.format:
            return datatype.format if isinstance(datatype.format, (dict, OrderedDict)) \
                else dict(pattern=datatype.format)
        return {}

    @staticmethod
    def to_python(v, pattern=None, decimalChar=None, groupChar=None):
        if groupChar:
            v = v.replace(groupChar, '')
        if decimalChar and decimalChar != '.':
            v = v.replace(decimalChar, '.')
        return Decimal(v)

    @staticmethod
    def to_string(v, pattern=None, decimalChar=None, groupChar=None):
        fmt = '{0}' if groupChar is None else '{0:,}'
        v = fmt.format(v)
        if groupChar or decimalChar:
            def repl(m):
                if m.group('c') == ',':
                    return groupChar
                if m.group('c') == '.':
                    return decimalChar
            r = '(?P<c>[{0}])'.format(re.escape((decimalChar or '') + (groupChar or '')))
            v = re.sub(r, repl, v)
        return v


class integer(decimal):
    name = 'integer'

    @staticmethod
    def to_python(v, **kw):
        return int(decimal.to_python(v, **kw))


class _float(anyAtomicType):
    name = 'float'

    @staticmethod
    def to_python(v, **kw):
        return float(v)

    @staticmethod
    def to_string(v, **kw):
        return '{0}'.format(v)


class number(_float):
    name = 'number'


class string(anyAtomicType):
    name = 'string'

    @staticmethod
    def derived_description(datatype):
        return dict(regex=re.compile(datatype.format) if datatype.format else None)

    @staticmethod
    def to_python(v, regex=None):
        if regex and not regex.match(v):
            raise ValueError()
        return v


class QName(string):
    name = 'QName'


class xml(string):
    name = 'xml'


class html(string):
    name = 'html'


class json(string):
    name = 'json'

    @staticmethod
    def to_python(v, **kw):
        return loads(v)

    @staticmethod
    def to_string(v, **kw):
        return dumps(v)


DATATYPES = {'any': anyAtomicType()}
# We register two levels of derived datatypes:
for cls in anyAtomicType.__subclasses__():
    DATATYPES[cls.name] = cls()
    for subcls in cls.__subclasses__():
        DATATYPES[subcls.name] = subcls()


def optional_int():
    return attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
        convert=lambda v: v if v is None else int(v))


@attr.s
class Datatype(DescriptionBase):
    """
    .. seealso:: http://w3c.github.io/csvw/metadata/#datatypes
    """
    base = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(DATATYPES)))
    format = attr.ib(default=None)
    length = optional_int()
    minLength = optional_int()
    maxLength = optional_int()
    minimum = attr.ib(default=None)
    maximum = attr.ib(default=None)
    minInclusive = attr.ib(default=None)
    maxInclusive = attr.ib(default=None)
    minExclusive = attr.ib(default=None)
    maxExclusive = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.length is not None:
            if self.minLength is not None and self.length < self.minLength:
                raise ValueError()

            if self.maxLength is not None:
                if self.length > self.maxLength:
                    raise ValueError()

        if self.minLength is not None and self.maxLength is not None \
                and self.minLength > self.maxLength:
            raise ValueError()

        if not isinstance(self.derived_description, dict):
            raise ValueError()  # pragma: no cover

    @classmethod
    def fromvalue(cls, v):
        """
        either a single string that is the main datatype of the values of the cell or a
        datatype description object.
        """
        if isinstance(v, cls):
            return v

        if isinstance(v, text_type):
            return cls(base=v)

        if isinstance(v, (dict, OrderedDict)):
            return cls(**DescriptionBase.partition_properties(v))

        raise ValueError(v)

    def asdict(self, omit_defaults=True):
        res = DescriptionBase.asdict(self, omit_defaults=omit_defaults)
        if len(res) == 1 and 'base' in res:
            return res['base']
        return res

    @property
    def basetype(self):
        return DATATYPES[self.base]

    @property
    def derived_description(self):
        return self.basetype.derived_description(self)

    def formatted(self, v):
        return self.basetype.to_string(v, **self.derived_description)

    def parse(self, v):
        return self.basetype.to_python(v, **self.derived_description)

    def validate(self, v):
        try:
            l = len(v or '')
            if self.length is not None and l != self.length:
                raise ValueError()
            if self.minLength is not None and l < self.minLength:
                raise ValueError()
            if self.maxLength is not None and l > self.maxLength:
                raise ValueError()
        except TypeError:
            pass
        if isinstance(self.basetype, (decimal, _float, date, dateTime)):
            if self.minimum is not None and v < self.minimum:
                raise ValueError()
            if self.maximum is not None and v > self.maximum:
                raise ValueError()
        return v

    def read(self, v):
        return self.validate(self.parse(v))


@attr.s
class Description(DescriptionBase):
    """
    Adds support for inherited properties.

    .. seealso:: http://w3c.github.io/csvw/metadata/#inherited-properties
    """
    # To be able to resolve inheritance chains, we also provide a place to store a
    # reference to the containing object:
    _parent = attr.ib(default=None, repr=False)

    aboutUrl = uri_template_property()
    datatype = attr.ib(
        default=None,
        convert=lambda v: v if not v else Datatype.fromvalue(v))
    default = attr.ib(default="")
    lang = attr.ib(default="und")
    null = attr.ib(default="")
    ordered = attr.ib(default=None)
    propertyUrl = uri_template_property()
    required = attr.ib(default=None)
    separator = attr.ib(default=None)
    textDirection = attr.ib(default=None)
    valueUrl = uri_template_property()

    def inherit(self, attr):
        v = getattr(self, attr)
        if v is None and self._parent:
            return getattr(self._parent, attr)
        return v


@attr.s
class Column(UnicodeMixin, Description):
    name = attr.ib(
        default=None,
        validator=attrlib.valid_re(_varname, nullable=True))
    suppressOutput = attr.ib(default=False)
    titles = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(NaturalLanguage)),
        convert=lambda v: v if v is None else NaturalLanguage(v))
    virtual = attr.ib(default=False)
    _number = attr.ib(default=None, repr=False)

    def __unicode__(self):
        return self.name or \
            (self.titles and self.titles.getfirst()) or \
            '_col.{0}'.format(self._number)


@attr.s
class Schema(Description):
    columns = attr.ib(
        default=attr.Factory(list),
        convert=lambda v: [Column.fromvalue(c) for c in v])
    foreignKeys = attr.ib(default=attr.Factory(list))
    primaryKey = attr.ib(default=None)
    rowTitles = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        for i, col in enumerate(self.columns):
            col._parent = self
            col._number = i + 1


@attr.s
class TableLike(Description):
    dialect = attr.ib(
        default=None, convert=lambda v: Dialect(**v) if isinstance(v, dict) else v)
    notes = attr.ib(default=attr.Factory(list))
    tableDirection = attr.ib(
        default='auto',
        validator=attr.validators.in_(['rtl', 'ltr', 'auto']))
    tableSchema = attr.ib(
        default=None,
        convert=lambda v: Schema.fromvalue(v))
    transformations = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        if self.tableSchema:
            self.tableSchema._parent = self


@attr.s
class Table(TableLike):
    url = attr.ib(
        default=None,
        validator=attr.validators.instance_of(Link),
        convert=lambda v: Link(v))
    suppressOutput = attr.ib(default=False)

    @cached_property()
    def colspec(self):
        spec = {}
        for col in self.tableSchema.columns:
            desc = Description(**{
                attr: col.inherit(attr)
                for attr in ['datatype', 'lang', 'null', 'required', 'separator']})
            desc = ('{0}'.format(col), desc)
            spec['{0}'.format(col)] = desc
            if col.titles:
                spec.setdefault(col.titles.getfirst(), desc)
        return spec

    def __iter__(self):
        dialect = self.dialect or self._parent.dialect or Dialect()
        fname = self.url.resolve(self._parent.base)

        if dialect.header:
            items = reader(fname, dialect=dialect, dicts=True)
        else:
            header = [
                '{0}'.format(col) for col in self.tableSchema.columns if not col.virtual]
            items = [
                OrderedDict(zip(header, row)) for row in reader(fname, dialect=dialect)]

        for item in items:
            res = OrderedDict()
            for k, v in item.items():
                # see http://w3c.github.io/csvw/syntax/#parsing-cells
                name, spec = self.colspec.get(k, (None, None))
                if name:
                    k = name
                if spec:
                    if v == '':
                        if spec.required:
                            raise ValueError('required column value is missing')
                        v = spec.default

                    if spec.separator:
                        if v == '':
                            v = []
                        else:
                            if v == spec.null:
                                v = None
                            else:
                                v = v.split(spec.separator)
                                v = [spec.default if vv is '' else vv for vv in v]
                                v = [None if vv == spec.null else vv for vv in v]
                    else:
                        if v == spec.null:
                            if spec.required:
                                raise ValueError('required column value is missing')
                            v = None

                    if spec.datatype:
                        if isinstance(v, list):
                            v = [spec.datatype.read(vv) for vv in v]
                        else:
                            v = spec.datatype.read(v)
                res[k] = v
            yield res


@attr.s
class TableGroup(TableLike):
    _fname = attr.ib(default=None)
    url = attr.ib(default=None)
    tables = attr.ib(
        repr=False,
        default=attr.Factory(list),
        convert=lambda v: [Table.fromvalue(vv) for vv in v])

    def __attrs_post_init__(self):
        TableLike.__attrs_post_init__(self)
        for table in self.tables:
            table._parent = self

    @property
    def base(self):
        return self._fname.parent

    @classmethod
    def from_file(cls, fname):
        res = cls.fromvalue(load(fname))
        res._fname = Path(fname)
        return res

    def to_file(self, fname, omit_defaults=True):
        dump(self.asdict(omit_defaults=omit_defaults), fname, indent=4)
        return fname
