# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase

from clldutils.testing import capture


class Tests(TestCase):
    def test_ArgumentParser(self):
        from clldutils.clilib import ArgumentParser, ParserError

        def cmd(args):
            """
            docstring
            """
            if len(args.args) < 1:
                raise ParserError('not enough arguments')
            print(args.args[0])

        parser = ArgumentParser('pkg', cmd)

        with capture(parser.main, args=['help', 'cmd']) as out:
            self.assertIn('docstring', out)

        with capture(parser.main, args=['cmd', 'arg']) as out:
            self.assertIn('arg', out)

        self.assertEqual(parser.main(args=['cmd', 'arg']), 0)

        with capture(parser.main, args=['cmd']) as out:
            self.assertIn('not enough arguments', out)

    def test_cmd_error(self):
        from clldutils.clilib import ArgumentParser

        def cmd(args):
            raise ValueError

        parser = ArgumentParser('pkg', cmd)
        with self.assertRaises(ValueError):
            parser.main(args=['cmd'])

        self.assertEqual(parser.main(args=['cmd'], catch_all=True), 1)
