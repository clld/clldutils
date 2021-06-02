"""Badges for inclusion in markdown docs, etc.

.. seealso:: http://shields.io/
"""
from urllib.parse import urlencode, quote

__all__ = ['Colors', 'badge']


class Colors(object):
    """
    Colors available for shields.io badges.
    """
    brightgreen = 'brightgreen'
    green = 'green'
    yellowgreen = 'yellowgreen'
    yellow = 'yellow'
    orange = 'orange'
    red = 'red'
    lightgrey = 'lightgrey'
    blue = 'blue'


def badge(subject, status, color, fmt='svg', markdown=True, label=None, **kw) -> str:
    """
    URL for (or markdown markup to include) a badge from shields.io

    :param str subject: Text for the left side of the badge
    :param str status: Text for the right side of the badge
    :param str color: Color for the right side of the badge
    :param str fmt: `'svg'` or `'json'`
    :param bool markdown: If `True`, return a markdown image link, else return a URL
    :param str|None label: Link label, if `markdown==True`
    """
    label = label or ': '.join([subject, status])
    url = 'https://img.shields.io/badge/{0}-{1}-{2}.{3}{4}'.format(
        quote(subject), quote(status), color, fmt, '?' + urlencode(kw) if kw else '')
    return '![{0}]({1} "{0}")'.format(label, url) if markdown else url
