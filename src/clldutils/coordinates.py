"""
Functionality to convert between different representations of geo-coordinates.

In particular, we support conversion of coordinates in the notation used for the World Atlas of
Language Structures, e.g. (12d10N, 92d49E), to floating point latitude and longitude values.
"""
import re
import enum
import math
from typing import Union, Optional
import dataclasses

__all__ = ['Coordinates', 'dec2degminsec', 'degminsec2dec', 'degminsec']

DEGREES = "°"
MINUTES = "\u2032"
SECONDS = "\u2033"
DimensionType = Union[str, int, float]
DEGMINSEC_FMT = (r'(?P<deg>\d+)\s*' + DEGREES + r'\s*'
                 r'((?P<min>\d+)\s*' + MINUTES + r'\s*)?'
                 r'((?P<sec>[\d.]+)\s*' + SECONDS + r'\s*)?')

PATTERNS = {
    'lat_alnum': re.compile(r"(?P<deg>\d+)d(?P<min>[0-9]+)?(?P<sec>'\d+'')?(?P<hem>S|N)"),
    'lon_alnum': re.compile(r"(?P<deg>\d+)d(?P<min>\d+)?(?P<sec>'\d+'')?(?P<hem>E|W)"),
    'lat_degminsec': re.compile(DEGMINSEC_FMT + r'(?P<hem>S|N)'),
    'lon_degminsec': re.compile(DEGMINSEC_FMT + r'(?P<hem>E|W)'),
}


class CoordinateFormat(enum.Enum):
    """Formatting options for coordinates."""
    alnum = enum.auto()  # pylint: disable=invalid-name
    ascii = enum.auto()  # pylint: disable=invalid-name
    degminsec = enum.auto()  # pylint: disable=invalid-name


def get_format(what: [str, CoordinateFormat]) -> CoordinateFormat:
    """Allow retrieving a CoordinateFormat by name."""
    if isinstance(what, str):
        return getattr(CoordinateFormat, what)
    return what


CoordinateFormatType = Union[CoordinateFormat, str]


@dataclasses.dataclass
class DegMinSec:
    """A coordinate datum as triple."""
    degrees: int
    minutes: int
    seconds: float

    @classmethod
    def from_match(cls, m: re.Match) -> 'DegMinSec':
        """Use the groups of a pattern as defined in PATTERNS to create an instance."""
        return cls(int(m.group('deg') or 0), int(m.group('min') or 0), float(m.group('sec') or 0.0))

    def as_string(
            self,
            hemisphere: str,
            format: CoordinateFormatType,  # pylint: disable=redefined-builtin
    ) -> str:
        """Format as string."""
        degrees, minutes, seconds = self.degrees, self.minutes, self.seconds
        seconds = int(round(seconds))
        if seconds == 60:
            minutes += 1
            seconds = 0

        if 120 > minutes >= 60:  # pragma: no cover
            # This case cannot really happen, because we only ever feed the results of
            # dec2degminsec into this method.
            degrees += 1
            minutes -= 60

        format = get_format(format)
        if format == CoordinateFormat.alnum:
            res = f"{degrees}d"
            if minutes:
                res += f"{minutes:02}"
            res += hemisphere
            return res

        if format == CoordinateFormat.ascii:
            res = f"{degrees}°"
            if minutes:
                res += f"{minutes:0>2d}'"
            if seconds:
                res += f'{seconds:0>2f}"'
            res += hemisphere
            return res

        res = f"{degrees}{DEGREES}"

        if minutes:
            res += f" {minutes}{MINUTES}"

        if seconds:
            res += f" {seconds}{SECONDS}"
        res += f" {hemisphere}"
        return res


def degminsec(dec, hemispheres: str, no_seconds: bool = False) -> str:
    """
    .. code-block:: python

        >>> degminsec(2.4, 'NS')
        "2°24'N"
        >>> degminsec(2.43, 'NS')
        '2°25\'48.000000"N'
        >>> degminsec(1.249, 'NS', no_seconds=True)
        "1°15'N"
    """
    if 'N' in hemispheres:
        return Coordinates(dec, 0).lat_to_string(
            format=CoordinateFormat.ascii, no_seconds=no_seconds)
    return Coordinates(0, dec).lon_to_string(
        format=CoordinateFormat.ascii, no_seconds=no_seconds)


def _dec2degminsec(dec: float, no_seconds: bool = False) -> DegMinSec:
    degrees = int(math.floor(dec))
    dec = (dec - int(math.floor(dec))) * 60
    minutes = int(math.floor(dec))
    dec = (dec - int(math.floor(dec))) * 60
    seconds = dec
    if no_seconds:
        if seconds > 30:
            if minutes < 59:
                minutes += 1
            else:
                minutes = 0
                degrees += 1
        seconds = 0
    return DegMinSec(degrees, minutes, seconds)


def dec2degminsec(dec: float, no_seconds: bool = False) -> tuple[int, int, float]:
    """
    convert a floating point number of degrees to a triple (int degrees, int minutes, float seconds)

    .. code-block:: python

        >>> assert dec2degminsec(30.50) == (30, 30, 0.0)
    """
    return dataclasses.astuple(_dec2degminsec(dec, no_seconds=no_seconds))


def _degminsec2dec(d: DegMinSec) -> float:
    dec = float(d.degrees)
    if d.minutes:
        dec += float(d.minutes) / 60
    if d.seconds:
        dec += float(d.seconds) / 3600
    return dec


def degminsec2dec(degrees: int, minutes: int, seconds: float) -> float:
    """
    convert a triple (int degrees, int minutes, float seconds) to a floating point number of degrees

    .. code-block:: python

        >>> assert dec2degminsec(degminsec2dec(30,30,0.0)) == (30,30,0.0)
    """
    return _degminsec2dec(DegMinSec(degrees, minutes, seconds))


class Coordinates:
    """
    A (lat, lon) pair, that can be represented in various formats.

    .. code-block:: python

        >>> c = Coordinates('13dN', 0)
        >>> assert c.latitude >= 13
        >>> assert c.latitude <= 13.1
        >>> c = Coordinates(0, 0)
        >>> assert c.lat_to_string() == '0dN'
        >>> assert c.lon_to_string() == '0dE'
        >>> c = Coordinates(12.17, 92.83)
        >>> assert c.lat_to_string() == '12d10N'
        >>> assert c.lon_to_string() == '92d49E'
        >>> c = Coordinates(-12.17, -92.83)
        >>> assert c.lat_to_string() == '12d10S'
        >>> c.lat_to_string(format=None)
        '12° 10′ 12″ S'
        >>> c.lat_to_string(format=CoordinateFormat.ascii)
        '12°10\'12.000000"S'
        >>> assert c.lon_to_string() == '92d49W'
        >>> lat, lon = '12d30N', '60d30E'
        >>> c = Coordinates(lat, lon)
        >>> assert c.lat_to_string() == lat
        >>> assert c.lon_to_string() == lon
    """

    def __init__(
            self,
            lat: DimensionType,
            lon: DimensionType,
            format: CoordinateFormatType = CoordinateFormat.alnum):  # pylint: disable=W0622
        format = get_format(format or CoordinateFormat.alnum)

        if isinstance(lat, float):
            self.latitude = lat
        elif isinstance(lat, int):
            self.latitude = float(lat)
        else:
            self.latitude = self.lat_from_string(lat, format)

        if isinstance(lon, float):
            self.longitude = lon
        elif isinstance(lon, int):
            self.longitude = float(lon)
        else:
            self.longitude = self.lon_from_string(lon, format)

    def _match(
            self, string: Union[str, bytes],
            type: str,  # pylint: disable=W0622
            format: CoordinateFormat,  # pylint: disable=W0622
    ) -> re.Match:
        if isinstance(string, bytes):
            string = string.decode('utf8')

        if type + '_' + format.name in PATTERNS:
            p = PATTERNS[type + '_' + format.name]
        else:
            p = PATTERNS[type + '_alnum']  # pragma: no cover

        m = p.match(string)
        if not m:
            raise ValueError(string)
        return m

    def lat_from_string(
            self,
            lat: str,
            format: CoordinateFormat = CoordinateFormat.alnum,  # pylint: disable=W0622
    ) -> float:
        """Parse a latitude value."""
        m = self._match(lat, 'lat', format)
        dec = _degminsec2dec(DegMinSec.from_match(m))
        if m.group('hem') == 'S':
            dec = -dec
        return dec

    def lon_from_string(
            self,
            lon: str,
            format: CoordinateFormat = CoordinateFormat.alnum,  # pylint: disable=W0622
    ) -> float:
        """Parse a longitude value."""
        m = self._match(lon, 'lon', format)
        dec = _degminsec2dec(DegMinSec.from_match(m))
        if m.group('hem') == 'W':
            dec = -dec
        return dec

    def lat_to_string(
            self,
            format: Optional[CoordinateFormat] = CoordinateFormat.alnum,  # pylint: disable=W0622
            no_seconds: bool = False,
    ) -> str:
        """A latitude value represented as string."""
        if self.latitude < 0:
            hemisphere = 'S'
        else:
            hemisphere = 'N'
        d = _dec2degminsec(abs(self.latitude), no_seconds=no_seconds)
        return d.as_string(hemisphere, format)

    def lon_to_string(
            self,
            format: Optional[CoordinateFormat] = CoordinateFormat.alnum,  # pylint: disable=W0622
            no_seconds: bool = False,
    ) -> str:
        """A longitude value represented as string."""
        if self.longitude < 0:
            hemisphere = 'W'
        else:
            hemisphere = 'E'
        d = _dec2degminsec(abs(self.longitude), no_seconds=no_seconds)
        return d.as_string(hemisphere, format)
