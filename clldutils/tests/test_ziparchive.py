# coding: utf8
from __future__ import unicode_literals, print_function, division

from clldutils.testing import WithTempDir


class Tests(WithTempDir):
    def test_ZipArchive(self):
        from clldutils.ziparchive import ZipArchive

        fname, text, name = self.tmp_path('test.zip'), 'äöüß', 'test'

        with ZipArchive(fname, mode='w') as archive:
            archive.write_text(text, name)

        with ZipArchive(fname) as archive:
            self.assertEqual(text, archive.read_text(name))
