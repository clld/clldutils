import pytest

from clldutils.coordinates import *


@pytest.mark.parametrize(
    'dec,hem,res,no_seconds',
    [
        (2.4, 'NS', "2°24'N", False),
        (-2.35467, 'EW', '2°21\'17.000000"W', False),
        (5.333333333333, 'NS', "5°20'N", True),
        (-9.999, 'EW', "10°W", True),
    ]
)
def test_degminsec(dec, hem, res, no_seconds):
    assert degminsec(dec, hem, no_seconds=no_seconds) == res


@pytest.mark.parametrize(
    'format,coord,lat,lon',
    [
        ('aln', ('13dN', 0), 13.0, 0),
        ('degminsec', ('1°1′1″N', '1°1′1.5″W'), 1.017, -1.017),
        ('degminsec', ('1°1′1″N'.encode('utf8'), '1°1′1.5″W'), 1.1, -1.1),
    ]
)
def test_to_dec(format, coord, lat, lon):
    c = Coordinates(coord[0], coord[1], format=format)
    assert pytest.approx(c.latitude, abs=0.1) == lat
    assert pytest.approx(c.longitude, abs=0.1) == lon


def test_bad_coords():
    with pytest.raises(ValueError):
        _ = Coordinates('13dxN', 0)


@pytest.mark.parametrize(
    'coord,lat,lon',
    [
        ((0, 0), '0dN', '0dE'),
        ((2.4, 0), '2d24N', '0dE'),
        ((12.17, 92.83), '12d10N', '92d49E'),
        ((-12.17, -92.83), '12d10S', '92d49W'),
        (('12d30N', '60d30E'), '12d30N', '60d30E'),
    ]
)
def test_to_alnum(coord, lat, lon):
    c = Coordinates(*coord)
    assert c.lat_to_string() == lat
    assert c.lon_to_string() == lon


def test_roundtrip():
    for lat in range(-90, 90):
        lat += 0.15
        c = Coordinates(lat, 0.222)
        c2 = Coordinates(
            c.lat_to_string('degminsec'), c.lon_to_string('degminsec'), format='degminsec')
        assert pytest.approx(lat) == c2.latitude

    for lon in range(-180, 180):
        lon += 0.44443444444
        c = Coordinates(-0.1111, lon)
        c2 = Coordinates(
            c.lat_to_string('degminsec'), c.lon_to_string('degminsec'), format='degminsec')
        assert pytest.approx(lon, abs=0.01) == c2.longitude
