# coding: utf8
from __future__ import unicode_literals
import unittest
from tempfile import mkdtemp
import shutil

from clldutils.path import Path


class WithTempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def tmp_path(self, *comps):
        return Path(self.tmp).joinpath(*comps)
