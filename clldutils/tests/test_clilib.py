# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase

from mock import patch, Mock

from clldutils.testing import capture, capture_all


class Tests(TestCase):
    def test_ArgumentParser(self):
        from clldutils.clilib import ArgumentParserWithLogging, ParserError, command

        def cmd(args):
            """
            docstring
            """
            if len(args.args) < 1:
                raise ParserError('not enough arguments')
            print(args.args[0])

        parser = ArgumentParserWithLogging('pkg', cmd)

        with capture(parser.main, args=['help', 'cmd']) as out:
            self.assertIn('docstring', out)

        with capture(parser.main, args=['cmd', 'arg']) as out:
            self.assertIn('arg', out)

        with capture_all(parser.main, args=['cmd', 'arg']) as res:
            self.assertEqual(res[0], 0)

        with capture(parser.main, args=['cmd']) as out:
            self.assertIn('not enough arguments', out)

        with capture_all(parser.main, args=['x']) as res:
            self.assertNotEqual(res[0], 0)
            self.assertTrue(res[1].startswith('invalid'))

        @command()
        def ls(args):
            """
            my name is ls
            """
            return

        @command(name='list')
        def f(args):
            """
            my name is list
            """
            return

        parser = ArgumentParserWithLogging('pkg')
        with capture(parser.main, args=['help', 'ls']) as out:
            self.assertIn('my name is ls', out)

        with capture(parser.main, args=['help', 'list']) as out:
            self.assertIn('my name is list', out)

        self.assertEqual(parser.main(args=['ls', 'arg']), 0)
        self.assertEqual(parser.main(args=['list', 'arg']), 0)

    def test_cmd_error(self):
        from clldutils.clilib import ArgumentParser

        def cmd(args):
            raise ValueError

        parser = ArgumentParser('pkg', cmd)
        with self.assertRaises(ValueError):
            parser.main(args=['cmd'])

        self.assertEqual(parser.main(args=['cmd'], catch_all=True), 1)

    def test_confirm(self):
        from clldutils.clilib import confirm

        with patch('clldutils.clilib.input', Mock(return_value='')):
            self.assertTrue(confirm('a?'))
            self.assertFalse(confirm('a?', default=False))

        with patch('clldutils.clilib.input', Mock(side_effect=['x', 'y'])):
            with capture_all(confirm, 'a?') as res:
                self.assertTrue(res[0])
                self.assertIn('Please respond', res[1])
