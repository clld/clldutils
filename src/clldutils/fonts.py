"""
`xhtml2pdf` provides a convenient way to create functional PDF programmatically from HTML.

In order to be able to use SIL's Charis fonts, these must be available locally and embedded
as explained in `<https://xhtml2pdf.readthedocs.io/en/latest/reference.html#using-custom-fonts>`_
To make this easier, `clldutils` packages the necessary true-type fonts and makes a suitable
font specification available via :func:`charis_font_spec_css`

To keep `clldutils` as small as possible, we only include the TrueType version of
Charis SIL 6.101 from 9 Feb 2022.
"""
import pathlib

from clldutils.html import HTML, literal

__all__ = ['FONTS_DIR', 'charis_font_spec_css', 'charis_font_spec_html']

FONTS_DIR = pathlib.Path(__file__).parent / 'fonts'


def charis_font_spec_css() -> str:
    """
    Font spec for using CharisSIL with Pisa (xhtml2pdf).

    If included, a `font-family` named "charissil" is defined.

    The paths inserted for the font files are absolute, local paths which can be resolved as
    links by `xhtml2pdf`. If you use a custom
    `link_callback <https://xhtml2pdf.readthedocs.io/en/latest/reference.html#link-callback>`_
    with `pisa.CreatePDF`, make sure to return unhandled `src_attr` arguments as is.
    """
    return """
    @font-face {{
        font-family: 'charissil';
        src: url('{0}/CharisSIL-Regular.ttf');
    }}
    @font-face {{
        font-family: 'charissil';
        font-style: italic;
        src: url('{0}/CharisSIL-Italic.ttf');
    }}
    @font-face {{
        font-family: 'charissil';
        font-weight: bold;
        src: url('{0}/CharisSIL-Bold.ttf');
    }}
    @font-face {{
        font-family: 'charissil';
        font-weight: bold;
        font-style: italic;
        src: url('{0}/CharisSIL-BoldItalic.ttf');
    }}
""".format(FONTS_DIR.resolve())


def charis_font_spec_html() -> HTML:
    """
    Charis SIL font specification inside an HTML style tag.
    """
    return HTML.style(literal(charis_font_spec_css()))
