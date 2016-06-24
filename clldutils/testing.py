# coding: utf8
from __future__ import unicode_literals
import unittest
from tempfile import mkdtemp
import sys
from contextlib import contextmanager

from six import StringIO

from clldutils.path import Path, rmtree


class WithTempDirMixin(object):
    """
    Composable test fixture providing access to a temporary directory.

    http://nedbatchelder.com/blog/201210/multiple_inheritance_is_hard.html
    """
    def setUp(self):
        super(WithTempDirMixin, self).setUp()
        self.tmp = Path(mkdtemp())

    def tearDown(self):
        rmtree(self.tmp, ignore_errors=True)
        super(WithTempDirMixin, self).tearDown()

    def tmp_path(self, *comps):
        return self.tmp.joinpath(*comps)


class WithTempDir(WithTempDirMixin, unittest.TestCase):
    """
    Backwards compatible test base class.
    """


@contextmanager
def capture(func, *args, **kw):
    out, sys.stdout = sys.stdout, StringIO()
    func(*args, **kw)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out
