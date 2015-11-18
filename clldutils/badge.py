# coding: utf8
"""
Badges for inclusion in markdown docs, etc.

.. seealso:: http://shields.io/
"""
from __future__ import unicode_literals
from six.moves.urllib.parse import urlencode, quote


class Colors(object):
    brightgreen = 'brightgreen'
    green = 'green'
    yellowgreen = 'yellowgreen'
    yellow = 'yellow'
    orange = 'orange'
    red = 'red'
    lightgrey = 'lightgrey'
    blue = 'blue'


def badge(subject, status, color, fmt='svg', markdown=True, **kw):
    query = ''
    if kw:
        query = '?' + urlencode(kw)
    url = 'https://img.shields.io/badge/{0}-{1}-{2}.{3}{4}'.format(
        quote(subject), quote(status), color, fmt, query)
    if markdown:
        return '![{0}]({1} "{0}")'.format(': '.join([subject, status]), url)
    return url
