"""
Provides functionality to create simple SVG icons or pie charts which can be used as map markers
e.g. with leaflet.
"""
import dataclasses
import math
from typing import Optional, Union
from xml.sax.saxutils import escape

import clldutils.misc
import clldutils.color
from clldutils.color import rgb_as_hex

__all__ = ['svg', 'data_url', 'icon', 'pie']


def svg(content: str, height: Optional[int] = None, width: Optional[int] = None) -> str:
    """
    Wrap `content` (some SVG XML) into a `svg` element with optional dimension attributes.

    :return: The full SVG XML as string.
    """
    height = f' height="{height}"' if height else ''
    width = f' width="{width}"' if width else ''
    return f"""\
<svg  xmlns="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink"{height}{width}>
  {content}
</svg>"""


def style(stroke: str = None, fill: str = None, stroke_width: str = '1px', opacity=None) -> str:
    """SVG style spec."""
    res = ''
    if fill:
        res += f'fill:{fill};'
    if stroke:
        res += (f'stroke:{stroke};stroke-width:{stroke_width};'
                f'stroke-linecap:round;stroke-linejoin:round;')
    else:
        res += 'stroke:none;'
    if opacity:
        res += f'opacity:{opacity};'
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
    style_ = style(stroke='black', fill=rgb_as_hex(spec[1:]), opacity=opacity)
    return svg(f'<{paths[spec[0]]} style="{style_}"/>', height=40, width=40)


@dataclasses.dataclass
class PieSpec:
    """Pie specified by center and radius."""
    cx: float
    cy: float
    r: float
    current_angle_rad: float = 0.0

    def endpoint(self):
        """
        Calculate position of point on circle given an angle, a radius, and the location
        of the center of the circle Zero line points west.
        """
        return (round(self.cx - (self.r * math.cos(self.current_angle_rad)), 1),
                round(self.cy - (self.r * math.sin(self.current_angle_rad)), 1))


def pie(
        data: list[Union[float, int]],
        colors: Optional[list[str]] = None,
        titles: Optional[list[str]] = None,
        width: int = 34,
        stroke_circle: bool = False,
) -> str:
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

    spec = PieSpec(cx=round(width / 2, 1), cy=round(width / 2, 1), r=round((width - 2) / 2, 1))

    svg_content = []
    titles = titles or [None] * len(data)
    stroke_circle = 'black' if stroke_circle is True else stroke_circle or 'none'

    def _iter_circle_content():
        f = rgb_as_hex(colors[0])
        yield (f'<circle cx="{spec.cx}" cy="{spec.cy}" r="{spec.r}" '
               f'style="stroke:{stroke_circle}; fill:{f};">')
        if titles[0]:
            yield f'<title>{escape(titles[0])}</title>'
        yield '</circle>'

    def _add_wedge(content, angle_deg, color, title):
        epcx, epcy = spec.endpoint()
        r1 = f"M{spec.cx},{spec.cy} L{epcx},{epcy}"
        spec.current_angle_rad += math.radians(angle_deg)
        epcx, epcy = spec.endpoint()
        arc = f"A{spec.r},{spec.r} 0 {1 if angle_deg > 180 else 0},1 {epcx} {epcy}"
        r2 = f"L{spec.cx},{spec.cy}"
        s = style(fill=rgb_as_hex(color))
        content.append(
            f'<path d="{r1} {arc} {r2}" style="{s}" transform="rotate(90 {spec.cx} {spec.cy})">')
        if title:
            content.append(f'<title>{escape(title)}</title>')
        content.append('</path>')

    if len(data) == 1:
        return svg(''.join(_iter_circle_content()), height=width, width=width)

    for angle_deg, color, title in zip([360.0 / sum(data) * d for d in data], colors, titles):
        _add_wedge(svg_content, angle_deg, color, title)

    if stroke_circle != 'none':
        svg_content.append(
            f'<circle cx="{spec.cx}" cy="{spec.cy}" r="{spec.r}" '
            f'style="stroke:{stroke_circle}; fill:none;"/>'
        )
    return svg(''.join(svg_content), height=width, width=width)
