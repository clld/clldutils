# coding: utf8
from __future__ import unicode_literals, print_function, division
import argparse
import logging
from collections import OrderedDict

from six.moves import input

from clldutils.loglib import Logging, get_colorlog


class ParserError(Exception):
    pass


# Global registry for commands.
# Note: This registry is global so it can only be used for one ArgumentParser instance.
# Otherwise, different ArgumentParsers will share the same sub-commands which will rarely
# be intended.
_COMMANDS = []


class Command(object):
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or func.__name__

    @property
    def doc(self):
        return self.func.__doc__

    def __call__(self, args):
        return self.func(args)


def command(name=None):
    def wrap(f):
        _COMMANDS.append(Command(f, name=name))
        return f
    return wrap


def _attr(obj, attr):
    return getattr(obj, attr, getattr(obj, '__{0}__'.format(attr), None))


class ArgumentParser(argparse.ArgumentParser):
    """
    A command line argument parser supporting sub-commands in a simple way.

    Sub-commands can be registered in one of two ways:
    - Passing functions as positional arguments into `ArgumentParser.__init__`.
    - Decorating functions with the `command` decorator.
    """
    def __init__(self, pkg_name, *commands, **kw):
        commands = commands or _COMMANDS
        kw.setdefault(
            'description', "Main command line interface of the %s package." % pkg_name)
        kw.setdefault(
            'epilog', "Use '%(prog)s help <cmd>' to get help about individual commands.")
        argparse.ArgumentParser.__init__(self, **kw)
        self.commands = OrderedDict([(_attr(cmd, 'name'), cmd) for cmd in commands])
        self.pkg_name = pkg_name
        self.add_argument("--verbosity", help="increase output verbosity")
        self.add_argument('command', help=' | '.join(self.commands.keys()))
        self.add_argument('args', nargs=argparse.REMAINDER)

    def main(self, args=None, catch_all=False, parsed_args=None):
        args = parsed_args or self.parse_args(args=args)
        if args.command == 'help' and len(args.args):
            # As help text for individual commands we simply re-use the docstrings of the
            # callables registered for the command:
            print(_attr(self.commands[args.args[0]], 'doc'))
        else:
            if args.command not in self.commands:
                print('invalid command')
                self.print_help()
                return 64
            try:
                self.commands[args.command](args)
            except ParserError as e:
                print(e)
                print(_attr(self.commands[args.command], 'doc'))
                return 64
            except Exception as e:
                if catch_all:
                    print(e)
                    return 1
                raise
        return 0


class ArgumentParserWithLogging(ArgumentParser):
    def __init__(self, pkg_name, *commands, **kw):
        super(ArgumentParserWithLogging, self).__init__(pkg_name, *commands, **kw)
        self.add_argument('--log', default=get_colorlog(pkg_name), help=argparse.SUPPRESS)
        self.add_argument(
            '--log-level',
            default=logging.INFO,
            help='log level [ERROR|WARN|INFO|DEBUG]',
            type=lambda x: getattr(logging, x))

    def main(self, args=None, catch_all=False, parsed_args=None):
        args = parsed_args or self.parse_args(args=args)
        with Logging(args.log, level=args.log_level):
            return super(ArgumentParserWithLogging, self).main(
                catch_all=catch_all, parsed_args=args)


def confirm(question, default=True):
    """Ask a yes/no question interactively.

    :param question: The text of the question to ask.
    :returns: True if the answer was "yes", False otherwise.
    """
    valid = {"": default, "yes": True, "y": True, "no": False, "n": False}
    while 1:
        choice = input(question + (" [Y/n] " if default else " [y/N] ")).lower()
        if choice in valid:
            return valid[choice]
        print("Please respond with 'y' or 'n' ")
