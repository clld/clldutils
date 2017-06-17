# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
from collections import OrderedDict
import json
import datetime
from decimal import Decimal

import clldutils
from clldutils.path import Path, copy, write_text, read_text
from clldutils.testing import WithTempDir
from clldutils import jsonlib

FIXTURES = Path(clldutils.__file__).parent.joinpath('tests', 'fixtures')


class NaturalLanguageTests(TestCase):
    def test_string(self):
        from clldutils.dsv_metadata import NaturalLanguage

        l = NaturalLanguage('abc')
        self.assertEqual(l.getfirst(), 'abc')
        self.assertEqual(l.get(None), ['abc'])
        self.assertEqual('{0}'.format(l), 'abc')

    def test_array(self):
        from clldutils.dsv_metadata import NaturalLanguage

        l = NaturalLanguage(['abc', 'def'])
        self.assertEqual(l.getfirst(), 'abc')
        self.assertEqual(l.get(None), ['abc', 'def'])
        self.assertEqual('{0}'.format(l), 'abc')

    def test_object(self):
        from clldutils.dsv_metadata import NaturalLanguage

        l = NaturalLanguage(OrderedDict([('en', ['abc', 'def']), ('de', 'äöü')]))
        self.assertEqual(l.getfirst('de'), 'äöü')
        self.assertEqual(l.get('en'), ['abc', 'def'])
        self.assertEqual('{0}'.format(l), 'abc')

    def test_error(self):
        from clldutils.dsv_metadata import NaturalLanguage

        with self.assertRaises(ValueError):
            NaturalLanguage(1)

    def test_serialize(self):
        from clldutils.dsv_metadata import NaturalLanguage

        l = NaturalLanguage('ä')
        self.assertEqual(json.dumps(l.asdict()), '"\\u00e4"')
        l.add('a')
        self.assertEqual(json.dumps(l.asdict()), '["\\u00e4", "a"]')
        l.add('ö', 'de')
        self.assertEqual(
            json.dumps(l.asdict()), '{"und": ["\\u00e4", "a"], "de": "\\u00f6"}')


class LinkTests(TestCase):
    def test_link(self):
        from clldutils.dsv_metadata import Link

        l = Link('a.csv')
        self.assertEqual('{0}'.format(l), l.resolve(None))
        self.assertEqual('http://example.org/a.csv', l.resolve('http://example.org'))
        base = Path('.')
        self.assertEqual(base, l.resolve(base).parent)


class DatatypeTests(TestCase):
    def _make_one(self, value):
        from clldutils.dsv_metadata import Datatype

        return Datatype.fromvalue(value)

    def test_string(self):
        t = self._make_one({'base': 'string', 'format': '[0-9]+[a-z]+'})
        self.assertEqual(t.read('1a'), '1a')
        with self.assertRaises(ValueError):
            t.read('abc')

    def test_number(self):
        t = self._make_one('integer')
        self.assertEqual(t.parse('5'), 5)

        t = self._make_one({'base': 'integer', 'minimum': 5, 'maximum': 10})
        v = t.parse('3')
        with self.assertRaises(ValueError):
            t.validate(v)
        self.assertEqual(t.formatted(v), '3')
        with self.assertRaises(ValueError):
            t.validate(12)

        t = self._make_one(
            {'base': 'decimal', 'format': {'groupChar': '.', 'decimalChar': ','}})
        self.assertEqual(t.parse('1.234,567'), Decimal('1234.567'))
        self.assertEqual(t.formatted(Decimal('1234.567')), '1.234,567')

    def test_object(self):
        t = self._make_one({'base': 'string', 'length': 5, '@id': 'x', 'dc:type': ''})
        self.assertEqual(t.validate('abcde'), 'abcde')
        with self.assertRaises(ValueError):
            t.validate('abc')

    def test_errors(self):
        with self.assertRaises(ValueError):
            self._make_one({'base': 'string', 'length': 5, 'minLength': 6})

        with self.assertRaises(ValueError):
            self._make_one({'base': 'string', 'length': 5, 'maxLength': 4})

        with self.assertRaises(ValueError):
            dt = self._make_one({'base': 'string', 'minLength': 4})
            dt.validate('abc')

        with self.assertRaises(ValueError):
            dt = self._make_one({'base': 'string', 'maxLength': 4})
            dt.validate('abcdefg')

        with self.assertRaises(ValueError):
            self._make_one({'base': 'string', 'maxLength': 5, 'minLength': 6})

        with self.assertRaises(ValueError):
            self._make_one(5)

    def test_date(self):
        t = self._make_one('date')
        self.assertEqual(t.formatted(t.parse('2012-12-01')), '2012-12-01')

        with self.assertRaises(ValueError):
            self._make_one({'base': 'date', 'format': '2012+12+12'})

        t = self._make_one('datetime')
        self.assertEqual(
            t.formatted(t.parse('2012-12-01T12:12:12')), '2012-12-01T12:12:12')

        with self.assertRaises(ValueError):
            self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm:ss.SGS'})

        with self.assertRaises(ValueError):
            self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm:ss.S XxX'})

        t = self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm'})
        self.assertEqual(
            t.formatted(t.parse('22.3.2015 22:05')), '22.3.2015 22:05')

        t = self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm:ss.SSS'})
        self.assertEqual(
            t.formatted(t.parse('22.3.2015 22:05:55.012')), '22.3.2015 22:05:55.012')
        self.assertEqual(
            t.formatted(datetime.datetime(2012, 12, 12, 12, 12, 12, microsecond=12345)),
            '12.12.2012 12:12:12.012')

        t = self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm X'})
        self.assertEqual(
            t.formatted(t.parse('22.3.2015 22:05 +03')), '22.3.2015 22:05 +03')

        t = self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm XXX'})
        self.assertEqual(
            t.formatted(t.parse('22.3.2015 22:05 +03:30')), '22.3.2015 22:05 +03:30')

        t = self._make_one({'base': 'datetime', 'format': 'd.M.yyyy HH:mm X'})
        self.assertEqual(
            t.formatted(t.parse('22.3.2015 22:05 +0330')), '22.3.2015 22:05 +0330')
        self.assertEqual(
            t.parse('22.3.2015 23:05 +0430'), t.parse('22.3.2015 22:05 +0330'))

        # "d.M.yyyy",  # e.g., 22.3.2015
        t = self._make_one({'base': 'date', 'format': "d.M.yyyy"})
        self.assertEqual(t.formatted(t.parse('22.3.2015')), '22.3.2015')

        t = self._make_one({'base': 'dateTimeStamp'})
        with self.assertRaises(ValueError):
            t.parse('22.3.2015 22:05')
        self.assertEqual(
            t.formatted(t.parse('2012-12-01T12:12:12.123456+05:30')),
            '2012-12-01T12:12:12.123456+05:30')

        with self.assertRaises(ValueError):
            self._make_one({'base': 'dateTimeStamp', 'format': 'd.M.yyyy HH:mm:ss.SSS'})

        t = self._make_one({'base': 'duration'})
        self.assertEqual(t.formatted(t.parse('P1Y1D')), 'P1Y1D')

        t = self._make_one({'base': 'duration'})
        self.assertEqual(t.formatted(t.parse('PT2H30M')), 'PT2H30M')

        t = self._make_one({'base': 'duration', 'format': 'P[1-5]Y'})
        with self.assertRaises(ValueError):
            t.parse('P8Y')

    def test_misc(self):
        t = self._make_one({'base': 'any'})
        self.assertEqual(t.formatted(None), 'None')

        t = self._make_one({'base': 'float'})
        self.assertAlmostEqual(t.parse('3.5'), 3.5)
        self.assertEqual(t.formatted(3.5), '3.5')

        t = self._make_one({'base': 'number'})
        self.assertAlmostEqual(t.parse('3.123456789'), 3.123456789)
        self.assertEqual(t.formatted(3.123456789), '3.123456789')

        t = self._make_one({'base': 'json'})
        self.assertEqual(t.parse('{"a": 5}'), dict(a=5))
        self.assertEqual(t.formatted(dict(a=5)), '{"a": 5}')

        t = self._make_one({'base': 'boolean'})
        with self.assertRaises(ValueError):
            t.parse('J')

        t = self._make_one({'base': 'boolean'})
        self.assertEqual('{0}'.format(t.basetype), 'boolean')
        self.assertEqual(t.parse(False), False)
        self.assertEqual(t.parse('false'), False)
        self.assertEqual(t.formatted(True), 'true')

        t = self._make_one({'base': 'boolean', 'format': 'J|N'})
        self.assertEqual(t.parse('J'), True)
        self.assertEqual(t.formatted(True), 'J')

        t = self._make_one({'base': 'binary'})
        self.assertEqual(t.formatted(t.parse('aGVsbG8gd29ybGQ=')), 'aGVsbG8gd29ybGQ=')
        with self.assertRaises(ValueError):
            t.parse('ä')
        with self.assertRaises(ValueError):
            t.parse('aGVsbG8gd29ybGQ')

        t = self._make_one({'base': 'hexBinary'})
        self.assertEqual(t.formatted(t.parse('abcdef12')), 'abcdef12')
        with self.assertRaises(ValueError):
            t.parse('ä')
        with self.assertRaises(ValueError):
            t.parse('a')


class TableGroupTests(WithTempDir):
    def _make_tablegroup(self, data=None):
        from clldutils.dsv_metadata import TableGroup

        md = self.tmp_path('md')
        copy(FIXTURES.joinpath('csv.txt-metadata.json'), md)
        write_text(
            self.tmp_path('csv.txt'), data or read_text(FIXTURES.joinpath('csv.txt')))
        return TableGroup.from_file(md)

    def test_roundtrip(self):
        t = self._make_tablegroup()
        self.assertEqual(
            jsonlib.load(t.to_file(self.tmp_path('out'))),
            jsonlib.load(FIXTURES.joinpath('csv.txt-metadata.json')))
        t.common_props['dc:title'] = 'the title'
        t.aboutUrl = 'http://example.org/{ID}'
        self.assertNotEqual(
            jsonlib.load(t.to_file(self.tmp_path('out'))),
            jsonlib.load(FIXTURES.joinpath('csv.txt-metadata.json')))
        self.assertNotEqual(
            jsonlib.load(t.to_file(self.tmp_path('out'), omit_defaults=False)),
            jsonlib.load(FIXTURES.joinpath('csv.txt-metadata.json')))

    def test_all(self):
        from clldutils.dsv_metadata import NaturalLanguage

        t = self._make_tablegroup()
        self.assertEqual(len(list(t.tables[0])), 2)

        t = self._make_tablegroup()
        t.tables[0].tableSchema.columns[1].null = 'line'
        self.assertIsNone(list(t.tables[0])[0]['_col.2'])

        t = self._make_tablegroup()
        t.tables[0].tableSchema.columns[1].separator = 'n'
        self.assertEqual(list(t.tables[0])[0]['_col.2'], ['li', 'e'])

        t = self._make_tablegroup()
        t.tables[0].tableSchema.columns[1].titles = NaturalLanguage('colname')
        self.assertIn('colname', list(t.tables[0])[0])

        t = self._make_tablegroup()
        t.dialect.header = True
        self.assertEqual(len(list(t.tables[0])), 1)

        t = self._make_tablegroup('abc,')
        t.tables[0].tableSchema.columns[0].required = True
        t.tables[0].tableSchema.columns[0].null = 'abc'
        with self.assertRaises(ValueError):
            list(t.tables[0])

        t = self._make_tablegroup(',')
        t.tables[0].tableSchema.columns[0].required = True
        with self.assertRaises(ValueError):
            list(t.tables[0])

    def test_separator(self):
        t = self._make_tablegroup('abc,')
        t.tables[0].tableSchema.columns[1].separator = ' '
        self.assertEqual(list(t.tables[0])[0]['_col.2'], [])

        t = self._make_tablegroup('abc,a')
        t.tables[0].tableSchema.columns[1].separator = ' '
        t.tables[0].tableSchema.columns[1].null = 'a'
        self.assertIsNone(list(t.tables[0])[0]['_col.2'])
