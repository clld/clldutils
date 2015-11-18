# coding: utf8
from __future__ import unicode_literals
import unittest


class Tests(unittest.TestCase):
    def test_as_posix(self):
        from clldutils.path import as_posix, Path

        self.assertRaises(ValueError, as_posix, 5)
        self.assertEquals(as_posix('.'), as_posix(Path('.')))
