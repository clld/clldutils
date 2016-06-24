# coding: utf8
from __future__ import unicode_literals, print_function, division
import unittest


class Tests(unittest.TestCase):
    def test_WithTempDir(self):
        from clldutils.testing import WithTempDirMixin

        class BaseTest(unittest.TestCase):
            def setUp(self):
                self.a = 1
                super(BaseTest, self).setUp()

        class Tests(WithTempDirMixin, BaseTest):
            def runTest(self):
                pass  # pragma: no cover

        test = Tests()
        test.setUp()
        self.assertTrue(hasattr(test, 'tmp_path'))
        self.assertTrue(hasattr(test, 'a'))
        self.assertTrue(test.tmp_path().exists())
