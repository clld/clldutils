# coding: utf8
from __future__ import unicode_literals, print_function, division
import unittest
import sys


class Tests(unittest.TestCase):
    def test_capture_all(self):
        from clldutils.testing import capture_all, capture

        def func():
            print('hello')
            print('world', file=sys.stderr)
            return 5

        with capture_all(func) as res:
            ret, out, err = res
            self.assertEqual(ret, 5)
            self.assertEqual(out.strip(), 'hello')
            self.assertEqual(err.strip(), 'world')

        with capture(func) as out:
            self.assertEqual(out.strip(), 'hello')

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
