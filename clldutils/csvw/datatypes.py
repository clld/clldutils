"""
Datatypes

We model the hierarchy of basic datatypes using derived classes.

.. seealso:: http://w3c.github.io/csvw/metadata/#datatypes
"""
from __future__ import unicode_literals, print_function, division

import re
from json import loads, dumps
import datetime
from decimal import Decimal, InvalidOperation
import base64
import binascii
from collections import OrderedDict

from dateutil import parser
import isodate
import rfc3986

from clldutils.misc import UnicodeMixin, to_binary


class anyAtomicType(UnicodeMixin):
    name = 'any'
    minmax = False

    @classmethod
    def value_error(cls, v):
        raise ValueError('invalid lexical value for {0}: {1}'.format(cls.name, v))

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


class string(anyAtomicType):
    name = 'string'

    @staticmethod
    def derived_description(datatype):
        # We wrap a regex soecified as `format` property into a group and add `$` to
        # make sure the whole string is matched when validating.
        return dict(regex=re.compile(
            '({0})$'.format(datatype.format)) if datatype.format else None)

    @staticmethod
    def to_python(v, regex=None):
        if regex and not regex.match(v):
            string.value_error(v)
        return v


class anyURI(string):
    name = 'anyURI'

    @staticmethod
    def to_python(v, regex=None):
        res = string.to_python(v, regex=regex)
        return rfc3986.uri.URIReference.from_string(res.encode('utf8'))

    @staticmethod
    def to_string(v, **kw):
        return v.unsplit()


class base64Binary(anyAtomicType):
    name = 'binary'

    @staticmethod
    def to_python(v, **kw):
        try:
            res = to_binary(v, encoding='ascii')
        except UnicodeEncodeError:
            base64Binary.value_error(v[:10])
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
            hexBinary.value_error(v[:10])
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
        if isinstance(s, bool) or s is None:
            return s
        if s in true:
            return True
        if s in false:
            return False
        raise boolean.value_error(s)

    @staticmethod
    def to_string(v, true=('true', '1'), false=('false', '0')):
        return true[0] if v else false[0]


class dateTime(anyAtomicType):
    name = 'datetime'
    minmax = True

    @staticmethod
    def derived_description(datatype):
        return dt_format_and_regex(datatype.format)

    @staticmethod
    def _parse(v, cls, regex, tz_marker=None):
        try:
            comps = regex.match(v).groupdict()
        except AttributeError:
            dateTime.value_error(v)
        if 'microsecond' in comps:
            # We have to convert decimal fractions of seconds to microseconds.
            # This is done by first chopping off anything under 6 decimal places,
            # then (in case we got less precision) right-padding with 0 to get a
            # 6-digit number.
            comps['microsecond'] = comps['microsecond'][:6].ljust(6, '0')
        res = cls(**{k: int(v) for k, v in comps.items()})
        if tz_marker:
            # Let dateutils take care of parsing the timezone info:
            res = res.replace(tzinfo=parser.parse(v).tzinfo)
        return res

    @staticmethod
    def to_python(v, regex=None, fmt=None, tz_marker=None):
        if regex is None:
            return parser.parse(v)
        return dateTime._parse(v, datetime.datetime, regex, tz_marker=tz_marker)

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


class _time(dateTime):
    name = 'time'

    @staticmethod
    def derived_description(datatype):
        return dt_format_and_regex(datatype.format or 'HH:mm:ss', no_date=True)

    @staticmethod
    def to_python(v, regex=None, fmt=None, tz_marker=None):
        assert regex is not None
        return dateTime._parse(v, datetime.time, regex, tz_marker=tz_marker)


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
    minmax = True

    _special = {
        'INF': 'Infinity',
        '-INF': '-Infinity',
        'NaN': 'NaN',
    }
    _reverse_special = {v: k for k, v in _special.items()}

    # TODO:
    # - use babel.numbers.NumberPattern.apply to format a value!
    # - use babel.numbers.parse_number to parse a value!
    @staticmethod
    def derived_description(datatype):
        if datatype.format:
            return datatype.format if isinstance(datatype.format, dict) \
                else dict(pattern=datatype.format)
        return {}

    @staticmethod
    def to_python(v, pattern=None, decimalChar=None, groupChar=None):
        if v in decimal._special:
            return Decimal(decimal._special[v])
        if groupChar:
            v = v.replace(groupChar, '')
        if decimalChar and decimalChar != '.':
            v = v.replace(decimalChar, '.')
        try:
            return Decimal(v)
        except (TypeError, InvalidOperation):
            decimal.value_error(v)

    @staticmethod
    def to_string(v, pattern=None, decimalChar=None, groupChar=None):
        if '{0}'.format(v) in decimal._reverse_special:
            return decimal._reverse_special['{0}'.format(v)]
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
    minmax = True

    @staticmethod
    def to_python(v, **kw):
        try:
            return float(v)
        except (TypeError, ValueError):
            _float.value_error(v)

    @staticmethod
    def to_string(v, **kw):
        return '{0}'.format(v)


class number(_float):
    name = 'number'


class QName(string):
    name = 'QName'


class gDay(string):
    name = 'gDay'


class gMonth(string):
    name = 'gMonth'


class gMonthDay(string):
    name = 'gMonthDay'


class gYear(string):
    name = 'gYear'


class gYearMonth(string):
    name = 'gYearMonth'


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


def dt_format_and_regex(fmt, no_date=False):
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

    if dt_sep:
        dfmt, tfmt = fmt.split(dt_sep)
    elif no_date:
        dfmt, tfmt = None, fmt
    else:
        dfmt, tfmt = fmt, None

    msecs = None  # The maximal number of decimal places for fractions of seconds.
    if tfmt and '.' in tfmt:  # There is a microseconds marker.
        tfmt, msecs = tfmt.split('.')  # Strip it off ...
        if set(msecs) != {'S'}:  # ... make sure it's valid ...
            raise ValueError(fmt)
        msecs = len(msecs)   # ... and store it's length.

    # Now we can check whether the bare date and time formats are valid:
    if (dfmt and dfmt not in date_patterns) or (tfmt and tfmt not in time_patterns):
        raise ValueError(fmt)

    regex, format = '', ''  # Initialize the output.

    if dfmt:
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

    if tfmt:
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
