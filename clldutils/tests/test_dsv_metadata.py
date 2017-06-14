# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase
from collections import OrderedDict
import json

import clldutils
from clldutils.path import Path, copy, write_text, read_text
from clldutils.testing import WithTempDir

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
        self.assertEqual(json.dumps(l.serialize()), '"\\u00e4"')
        l.add('a')
        self.assertEqual(json.dumps(l.serialize()), '["\\u00e4", "a"]')
        l.add('ö', 'de')
        self.assertEqual(
            json.dumps(l.serialize()), '{"und": ["\\u00e4", "a"], "de": "\\u00f6"}')


class LinkTests(TestCase):
    def test_link(self):
        from clldutils.dsv_metadata import Link

        l = Link('a.csv')
        self.assertEqual('{0}'.format(l), l.resolve(None))
        self.assertEqual('http://example.org/a.csv', l.resolve('http://example.org'))
        base = Path('.')
        self.assertEqual(base, l.resolve(base).parent)


class DatatypeTests(TestCase):
    def test_string(self):
        from clldutils.dsv_metadata import Datatype

        t = Datatype.fromvalue('integer')
        self.assertEqual(t.parse('5'), 5)

    def test_object(self):
        from clldutils.dsv_metadata import Datatype

        t = Datatype.fromvalue({'base': 'string', 'length': 5, '@id': 'x', 'dc:type': ''})
        self.assertEqual(t.validate('abcde'), 'abcde')
        with self.assertRaises(ValueError):
            t.validate('abc')

    def test_errors(self):
        from clldutils.dsv_metadata import Datatype

        with self.assertRaises(ValueError):
            Datatype.fromvalue({'base': 'string', 'length': 5, 'minLength': 6})

        with self.assertRaises(ValueError):
            Datatype.fromvalue({'base': 'string', 'length': 5, 'maxLength': 4})

        with self.assertRaises(ValueError):
            dt = Datatype.fromvalue({'base': 'string', 'minLength': 4})
            dt.validate('abc')

        with self.assertRaises(ValueError):
            dt = Datatype.fromvalue({'base': 'string', 'maxLength': 4})
            dt.validate('abcdefg')

        with self.assertRaises(ValueError):
            Datatype.fromvalue({'base': 'string', 'maxLength': 5, 'minLength': 6})

        with self.assertRaises(ValueError):
            Datatype.fromvalue(5)

    def test_boolean(self):
        from clldutils.dsv_metadata import Datatype

        t = Datatype.fromvalue({'base': 'integer', 'minimum': 5, 'maximum': 10})
        v = t.parse('3')
        with self.assertRaises(ValueError):
            t.validate(v)
        self.assertEqual(t.formatted(v), '3')
        with self.assertRaises(ValueError):
            t.validate(12)

        t = Datatype.fromvalue({'base': 'float'})
        self.assertAlmostEqual(t.parse('3.5'), 3.5)
        self.assertEqual(t.formatted(3.5), '3.5')

        t = Datatype.fromvalue({'base': 'json'})
        self.assertEqual(t.parse('{"a": 5}'), dict(a=5))
        self.assertEqual(t.formatted(dict(a=5)), '{"a": 5}')

        t = Datatype.fromvalue({'base': 'boolean'})
        with self.assertRaises(ValueError):
            t.parse('J')

        t = Datatype.fromvalue({'base': 'boolean'})
        self.assertEqual('{0}'.format(t.basetype), 'boolean')
        self.assertEqual(t.parse(False), False)
        self.assertEqual(t.parse('false'), False)
        self.assertEqual(t.formatted(True), 'true')

        t = Datatype.fromvalue({'base': 'boolean', 'format': 'J|N'})
        self.assertEqual(t.parse('J'), True)
        self.assertEqual(t.formatted(True), 'J')


class TableGroupTests(WithTempDir):
    def _make_tablegroup(self, data=None):
        from clldutils.dsv_metadata import TableGroup

        md = self.tmp_path('md')
        copy(FIXTURES.joinpath('csv.txt-metadata.json'), md)
        write_text(
            self.tmp_path('csv.txt'), data or read_text(FIXTURES.joinpath('csv.txt')))
        return TableGroup.from_file(md)

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
