"""
Functionality to convert between different representations of geo-coordinates.

In particular, we support conversion of coordinates in the notation used for the World Atlas of
Language Structures, e.g. (12d10N, 92d49E), to floating point latitude and longitude values.
"""
import re
import math

__all__ = ['Coordinates', 'dec2degminsec', 'degminsec2dec', 'degminsec']

import typing

DEGREES = "°"
MINUTES = "\u2032"
SECONDS = "\u2033"

PATTERNS = {
    'lat_alnum': re.compile(r"(?P<deg>\d+)d(?P<min>[0-9]+)?(?P<sec>'\d+'')?(?P<hem>S|N)"),
    'lon_alnum': re.compile(r"(?P<deg>\d+)d(?P<min>\d+)?(?P<sec>'\d+'')?(?P<hem>E|W)"),
    'lat_degminsec': re.compile(
        r'(?P<deg>\d+)\s*%s\s*((?P<min>\d+)\s*%s\s*)?((?P<sec>[\d.]+)\s*%s\s*)?(?P<hem>S|N)' % (
            DEGREES, MINUTES, SECONDS)),
    'lon_degminsec': re.compile(
        r'(?P<deg>\d+)\s*%s\s*((?P<min>\d+)\s*%s\s*)?((?P<sec>[\d.]+)\s*%s\s*)?(?P<hem>E|W)' % (
            DEGREES, MINUTES, SECONDS)),
}


def degminsec(dec, hemispheres: str, no_seconds: bool = False) -> str:
    """
    .. code-block:: python

        >>> degminsec(2.4, 'NS')
        "2°24'N"
        >>> degminsec(1.249, 'NS', no_seconds=True)
        "1°15'N"
    """
    if 'N' in hemispheres:
        return Coordinates(dec, 0).lat_to_string(format='ascii', no_seconds=no_seconds)
    return Coordinates(0, dec).lon_to_string(format='ascii', no_seconds=no_seconds)


def dec2degminsec(dec, no_seconds: bool = False) -> typing.Tuple[float, float, float]:
    """
    convert a floating point number of degrees to a triple (int degrees, int minutes, float seconds)

    .. code-block:: python

        >>> assert dec2degminsec(30.50) == (30, 30, 0.0)
    """
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
    return degrees, minutes, seconds


def degminsec2dec(degrees, minutes, seconds) -> float:
    """
    convert a triple (int degrees, int minutes, float seconds) to a floating point number of degrees

    .. code-block:: python

        >>> assert dec2degminsec(degminsec2dec(30,30,0.0)) == (30,30,0.0)
    """
    dec = float(degrees)
    if minutes:
        dec += float(minutes) / 60
    if seconds:
        dec += float(seconds) / 3600
    return dec


class Coordinates(object):
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
        >>> c.lat_to_string(format='ascii')
        '12°10\'12.000000"S'
        >>> assert c.lon_to_string() == '92d49W'
        >>> lat, lon = '12d30N', '60d30E'
        >>> c = Coordinates(lat, lon)
        >>> assert c.lat_to_string() == lat
        >>> assert c.lon_to_string() == lon
    """

    def __init__(self, lat, lon, format='alnum'):
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

    def _match(self, string, type, format):
        if isinstance(string, bytes):
            string = string.decode('utf8')

        if type + '_' + format in PATTERNS:
            p = PATTERNS[type + '_' + format]
        else:
            p = PATTERNS[type + '_alnum']

        m = p.match(string)
        if not m:
            raise ValueError(string)
        return m

    def lat_from_string(self, lat, format='alnum'):
        m = self._match(lat, 'lat', format)
        dec = degminsec2dec(m.group('deg'), m.group('min'), m.group('sec'))
        if m.group('hem') == 'S':
            dec = -dec
        return dec

    def lon_from_string(self, lon, format='alnum'):
        m = self._match(lon, 'lon', format)
        dec = degminsec2dec(m.group('deg'), m.group('min'), m.group('sec'))
        if m.group('hem') == 'W':
            dec = -dec
        return dec

    def _format(self, degrees, minutes, seconds, hemisphere, format):
        seconds = int(round(seconds))
        if seconds == 60:
            minutes += 1
            seconds = 0

        if 120 > minutes >= 60:  # pragma: no cover
            # This case cannot really happen, because we only ever feed the results of
            # dec2degminsec into this method.
            degrees += 1
            minutes -= 60

        if format == 'alnum':
            res = "%sd" % degrees
            if minutes:
                res += "%02d" % minutes
            res += hemisphere
            return res

        if format == 'ascii':
            res = "%s°" % degrees
            if minutes:
                res += "{0:0>2d}'".format(minutes)
            if seconds:
                res += '{0:0>2f}"'.format(seconds)
            res += hemisphere
            return res

        res = "%s%s" % (degrees, DEGREES)

        if minutes:
            res += " %s%s" % (minutes, MINUTES)

        if seconds:
            res += " %s%s" % (seconds, SECONDS)
        res += " %s" % hemisphere
        return res

    def lat_to_string(
            self, format: typing.Union[str, None] = 'alnum', no_seconds: bool = False) -> str:
        if self.latitude < 0:
            hemisphere = 'S'
        else:
            hemisphere = 'N'
        degrees, minutes, seconds = dec2degminsec(abs(self.latitude), no_seconds=no_seconds)
        return self._format(degrees, minutes, seconds, hemisphere, format)

    def lon_to_string(
            self, format: typing.Union[str, None] = 'alnum', no_seconds: bool = False) -> str:
        if self.longitude < 0:
            hemisphere = 'W'
        else:
            hemisphere = 'E'
        degrees, minutes, seconds = dec2degminsec(abs(self.longitude), no_seconds=no_seconds)
        return self._format(degrees, minutes, seconds, hemisphere, format)
