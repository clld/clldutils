# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase

from clldutils.testing import capture


class Tests(TestCase):
    def test_ArgumentParser(self):
        from clldutils.clilib import ArgumentParser

        def cmd(args):
            """
            docstring
            """
            print(args.args[0])

        parser = ArgumentParser('pkg', cmd)

        with capture(parser.main, args=['help', 'cmd']) as out:
            self.assertIn('docstring', out)

        with capture(parser.main, args=['cmd', 'arg']) as out:
            self.assertIn('arg', out)
