# coding: utf8
from __future__ import unicode_literals, print_function, division


def test_ZipArchive(tmppath):
    from clldutils.ziparchive import ZipArchive

    fname, text, name = tmppath / 'test.zip', 'äöüß', 'test'

    with ZipArchive(fname, mode='w') as archive:
        archive.write_text(text, name)

    with ZipArchive(fname) as archive:
        assert text == archive.read_text(name)
