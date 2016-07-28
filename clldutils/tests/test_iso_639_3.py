# coding: utf8
from __future__ import unicode_literals, print_function, division
import unittest

from mock import Mock, patch

import clldutils
from clldutils.path import copy, Path

FIXTURES = Path(clldutils.__file__).parent.joinpath('tests', 'fixtures')


class Tests(unittest.TestCase):
    def test_ISO(self):
        from clldutils.iso_639_3 import ISO

        def urlopen(*args, **kw):
            return Mock(read=Mock(
                return_value=' href="iso-639-3_Code_Tables_12345678.zip" '))

        def urlretrieve(url, dest):
            copy(FIXTURES.joinpath('iso.zip'), dest)

        with patch.multiple(
                'clldutils.iso_639_3', urlopen=urlopen, urlretrieve=urlretrieve):
            iso = ISO()
            self.assertIn('aab', iso)
