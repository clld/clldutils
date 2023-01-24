import re
import pathlib

from clldutils.fonts import *


def test_FONTS_DIR():
    assert FONTS_DIR.exists()


def test_charis_font_spec_css():
    for m in re.finditer(r"url\('([^']+)'\)", charis_font_spec_css()):
        assert pathlib.Path(m.groups()[0]).exists()


def test_charis_font_spec_html():
    assert '<style' in str(charis_font_spec_html())
