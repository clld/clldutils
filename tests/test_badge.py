# coding: utf8
from __future__ import unicode_literals
from functools import partial


def test_badge():
    from clldutils.badge import badge, Colors

    _badge = partial(badge, 'cov', '20%', Colors.orange)

    assert _badge() == \
        '![cov: 20%](https://img.shields.io/badge/cov-20%25-orange.svg "cov: 20%")'
    assert _badge(markdown=False, style='plastic') == \
        'https://img.shields.io/badge/cov-20%25-orange.svg?style=plastic'
    assert '[abc]' in badge('subject', 'status', 'color', label='abc')
