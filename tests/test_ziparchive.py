# coding: utf8
from __future__ import unicode_literals, print_function, division


def test_ZipArchive(tmpdir):
    from clldutils.ziparchive import ZipArchive

    fname, text, name = tmpdir.join('test.zip'), 'äöüß', 'test'

    with ZipArchive(str(fname), mode='w') as archive:
        archive.write_text(text, name)

    with ZipArchive(str(fname)) as archive:
        assert text == archive.read_text(name)
