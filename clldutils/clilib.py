# coding: utf8
from __future__ import unicode_literals, print_function, division
import argparse
from collections import OrderedDict


class ParserError(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):
    """
    An command line argument parser supporting sub-commands in a simple way.
    """
    def __init__(self, pkg_name, *commands, **kw):
        kw.setdefault(
            'description', "Main command line interface of the %s package." % pkg_name)
        kw.setdefault(
            'epilog', "Use '%(prog)s help <cmd>' to get help about individual commands.")
        argparse.ArgumentParser.__init__(self, **kw)
        self.commands = OrderedDict([(cmd.__name__, cmd) for cmd in commands])
        self.pkg_name = pkg_name
        self.add_argument("--verbosity", help="increase output verbosity")
        self.add_argument('command', help='|'.join(self.commands.keys()))
        self.add_argument('args', nargs=argparse.REMAINDER)

    def main(self, args=None, catch_all=False):
        args = self.parse_args(args=args)
        if args.command == 'help':
            # As help text for individual commands we simply re-use the docstrings of the
            # callables registered for the command:
            print(self.commands[args.args[0]].__doc__)
        else:
            try:
                self.commands[args.command](args)
            except ParserError as e:
                print(e)
                print(self.commands[args.command].__doc__)
                return 64
            except Exception as e:
                if catch_all:
                    print(e)
                    return 1
                raise
        return 0
