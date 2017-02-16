# coding: utf8
from __future__ import unicode_literals, print_function, division

from mock import Mock, patch

import clldutils
from clldutils.testing import WithTempDir
from clldutils.path import copy, Path

FIXTURES = Path(clldutils.__file__).parent.joinpath('tests', 'fixtures')


class Tests(WithTempDir):
    def test_ISO_download(self):
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

    def test_ISO(self):
        from clldutils.iso_639_3 import ISO, Code

        dated_zip = self.tmp_path('20121201.zip')
        copy(FIXTURES.joinpath('iso.zip'), dated_zip)
        iso = ISO(dated_zip)
        self.assertEqual('{0}'.format(iso), 'ISO 639-3 code tables from 2012-12-01')

        iso = ISO(FIXTURES.joinpath('iso.zip'))
        self.assertEqual('{0}'.format(iso), 'ISO 639-3 code tables from 2016-07-25')
        for attr in Code._type_map.values():
            self.assertIsInstance(getattr(iso, attr.lower()), list)

        self.assertEqual(len(iso.languages), 7)
        self.assertEqual(len(iso.macrolanguages[0].extension), 2)
        self.assertEqual(len(iso.languages[0].extension), 0)
        self.assertEqual(len(iso.retirements[0].change_to), 1)
        self.assertIn(iso['auv'].change_to[0], iso.languages)
        d = {iso['auv']: 1}
        self.assertIn(iso['auv'], d)
        self.assertIn('[twi]', repr(sorted(iso.values(), reverse=True)[0]))
        self.assertEqual('%s' % iso['aab'], 'Alumu-Tesu [aab]')
