# coding: utf8
from __future__ import unicode_literals
import unittest
from tempfile import mkdtemp
import sys
from contextlib import contextmanager

from six import StringIO

from clldutils.path import Path, rmtree


class WithTempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(mkdtemp())

    def tearDown(self):
        rmtree(self.tmp, ignore_errors=True)

    def tmp_path(self, *comps):
        return self.tmp.joinpath(*comps)


@contextmanager
def capture(func, *args, **kw):
    out, sys.stdout = sys.stdout, StringIO()
    func(*args, **kw)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out
