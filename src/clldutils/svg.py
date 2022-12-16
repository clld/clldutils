"""
Provides functionality to create simple SVG icons or pie charts which can be used as map markers
e.g. with leaflet.
"""
import math
import typing
from xml.sax.saxutils import escape

import clldutils.misc
import clldutils.color

from clldutils.color import rgb_as_hex

__all__ = ['svg', 'data_url', 'icon', 'pie']


def svg(content: str,
        height: typing.Optional[int] = None,
        width: typing.Optional[int] = None) -> str:
    """
    Wrap `content` (some SVG XML) into a `svg` element with optional dimension attributes.

    :return: The full SVG XML as string.
    """
    height = ' height="{0}"'.format(height) if height else ''
    width = ' width="{0}"'.format(width) if width else ''
    return """\
<svg  xmlns="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink"{0}{1}>
  {2}
</svg>""".format(height, width, content)


def style(stroke=None, fill=None, stroke_width='1px', opacity=None):
    res = ''
    if fill:
        res += 'fill:{0};'.format(fill)
    if stroke:
        res += 'stroke:{0};stroke-width:{1};stroke-linecap:round;stroke-linejoin:round;'\
            .format(stroke, stroke_width)
    else:
        res += 'stroke:none;'
    if opacity:
        res += 'opacity:{0};'.format(opacity)
    return res


def data_url(svgxml: str) -> str:
    """
    Turn SVG XML into a data URL suitable for inlining in HTML.
    """
    return clldutils.misc.data_url(svgxml, mimetype='image/svg+xml')


def icon(spec: str, opacity=None) -> str:
    """
    Creates a SVG graphic according to a spec as used for map icons in `clld` apps.

    :param spec: Icon spec of the form "(s|d|c|f|t)rrggbb" where the first character defines a \
    shape (s=square, d=diamond, c=circle, f=upside-down triangle, t=triangle) and "rrggbb" \
    specifies a color as hex triple.
    :return: SVG XML
    """
    paths = {
        's': 'path d="M8 8 H32 V32 H8 V8"',
        'd': 'path d="M20 2 L38 20 L20 38 L2 20 L20 2"',
        'c': 'circle cx="20" cy="20" r="14"',
        'f': 'path d="M2 4 L38 4 L20 35 L2 4"',
        't': 'path d="M2 36 L38 36 L20 5 L2 36"',
    }
    elem = '<{0} style="{1}"/>'.format(
        paths[spec[0]], style(stroke='black', fill=rgb_as_hex(spec[1:]), opacity=opacity))
    return svg(elem, height=40, width=40)


def pie(data: typing.List[typing.Union[float, int]],
        colors: typing.Optional[typing.List[str]] = None,
        titles: typing.Optional[typing.List[str]] = None,
        width: int = 34,
        stroke_circle: bool = False) -> str:
    """
    An SVG pie chart.

    :param data: list of numbers specifying the proportional sizes of the slices.
    :param colors: list of RGB colors as hex triplets, specifying the respective colors of the \
    slices.
    :param titles: list of strings to use as titles for the respective slices.
    :param width: Width of the SVG object.
    :param stroke_circle: Whether to stroke (aka outline) theboundary of the pie.
    :return: SVG XML representation of the data as pie chart.
    """
    colors = clldutils.color.qualitative_colors(len(data)) if colors is None else colors
    assert len(data) == len(colors)
    zipped = [(d, c) for d, c in zip(data, colors) if d != 0]
    data, colors = [z[0] for z in zipped], [z[1] for z in zipped]
    cx = cy = round(width / 2, 1)
    radius = round((width - 2) / 2, 1)
    current_angle_rad = 0
    svg_content = []
    total = sum(data)
    titles = titles or [None] * len(data)
    stroke_circle = 'black' if stroke_circle is True else stroke_circle or 'none'

    def endpoint(angle_rad):
        """
        Calculate position of point on circle given an angle, a radius, and the location
        of the center of the circle Zero line points west.
        """
        return (round(cx - (radius * math.cos(angle_rad)), 1),
                round(cy - (radius * math.sin(angle_rad)), 1))

    if len(data) == 1:
        svg_content.append(
            '<circle cx="{0}" cy="{1}" r="{2}" style="stroke:{3}; fill:{4};">'.format(
                cx, cy, radius, stroke_circle, rgb_as_hex(colors[0])))
        if titles[0]:
            svg_content.append('<title>{0}</title>'.format(escape(titles[0])))
        svg_content.append('</circle>')
        return svg(''.join(svg_content), height=width, width=width)

    for angle_deg, color, title in zip([360.0 / total * d for d in data], colors, titles):
        radius1 = "M{0},{1} L{2},{3}".format(cx, cy, *endpoint(current_angle_rad))
        current_angle_rad += math.radians(angle_deg)
        arc = "A{0},{1} 0 {2},1 {3} {4}".format(
            radius, radius, 1 if angle_deg > 180 else 0, *endpoint(current_angle_rad))
        radius2 = "L%s,%s" % (cx, cy)
        svg_content.append(
            '<path d="{0} {1} {2}" style="{3}" transform="rotate(90 {4} {5})">'.format(
                radius1, arc, radius2, style(fill=rgb_as_hex(color)), cx, cy))
        if title:
            svg_content.append('<title>{0}</title>'.format(escape(title)))
        svg_content.append('</path>')

    if stroke_circle != 'none':
        svg_content.append(
            '<circle cx="%s" cy="%s" r="%s" style="stroke:%s; fill:none;"/>'
            % (cx, cy, radius, stroke_circle))

    return svg(''.join(svg_content), height=width, width=width)
