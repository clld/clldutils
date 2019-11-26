import logging
import pkgutil
import pathlib
import argparse
import warnings
import importlib
import collections
import pkg_resources

import tabulate

from clldutils.loglib import Logging, get_colorlog
from clldutils import markup

__all__ = [
    'ParserError', 'Command', 'command', 'ArgumentParser', 'ArgumentParserWithLogging',
    'get_parser_and_subparsers', 'register_subcommands', 'add_format', 'Table', 'PathType',
]


class ParserError(Exception):
    pass


# Global registry for commands.
# Note: This registry is global so it can only be used for one ArgumentParser instance.
# Otherwise, different ArgumentParsers will share the same sub-commands which will rarely
# be intended.
_COMMANDS = []


class Command(object):

    def __init__(self, func, name=None, usage=None):
        self.func = func
        self.name = name or func.__name__
        self.usage = usage

    @property
    def doc(self):
        return self.usage or self.func.__doc__

    def __call__(self, args):
        return self.func(args)


def command(name=None, usage=None):
    def wrap(f):
        _COMMANDS.append(Command(f, name=name, usage=usage))
        return f
    return wrap


def _attr(obj, attr):
    return getattr(obj, attr, getattr(obj, '__{0}__'.format(attr), None))


class ArgumentParser(argparse.ArgumentParser):
    """A command line argument parser supporting sub-commands in a simple way.

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
        super(ArgumentParser, self).__init__(**kw)
        self.commands = collections.OrderedDict((_attr(cmd, 'name'), cmd) for cmd in commands)
        self.pkg_name = pkg_name
        self.add_argument("--verbosity", help="increase output verbosity")
        self.add_argument('command', help=' | '.join(self.commands))
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


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


def get_parser_and_subparsers(prog, with_defaults_help=True, with_log=True):
    kw = dict(prog=prog)
    if with_defaults_help:
        kw.update(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser = argparse.ArgumentParser(**kw)
    if with_log:
        parser.add_argument(
            '--log',
            default=get_colorlog(prog),
            help=argparse.SUPPRESS)
        parser.add_argument(
            '--log-level',
            default=logging.INFO,
            help='log level [ERROR|WARN|INFO|DEBUG]',
            type=lambda x: getattr(logging, x))

    subparsers = parser.add_subparsers(
        title="available commands",
        dest="_command",
        description='Run "COMAMND -h" to get help for a specific command.',
        metavar="COMMAND")
    return parser, subparsers


def iter_modules(pkg):
    """ Autodiscover and import all modules in a package.
    """
    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if not ispkg:
            modname = ".".join([pkg.__name__, name])
            try:
                yield name, importlib.import_module(modname)
            except Exception as e:  # pragma: no cover
                warnings.warn('{0} {1}'.format(e, modname))


def register_subcommands(subparsers, pkg, entry_point=None, formatter_class=Formatter):
    # Discover available commands:
    # Commands are identified by (<entry point name>).<module name>
    _cmds = collections.OrderedDict()
    _cmds.update(list(iter_modules(pkg)))
    if entry_point:
        # ... then look for commands provided in other packages:
        for ep in pkg_resources.iter_entry_points(entry_point):
            try:
                pkg = ep.load()
            except ImportError:
                warnings.warn('ImportError loading entry point {0.name}'.format(ep))
                continue
            _cmds.update(
                [('.'.join([ep.name, name]), mod) for name, mod in iter_modules(pkg)])

    for name, mod in _cmds.items():
        subparser = subparsers.add_parser(
            name,
            help=mod.__doc__.strip().splitlines()[0] if mod.__doc__.strip() else '',
            description=mod.__doc__,
            formatter_class=formatter_class)
        if hasattr(mod, 'register'):
            mod.register(subparser)
        subparser.set_defaults(main=mod.run)

    return _cmds


def add_format(parser, default='pipe'):
    parser.add_argument(
        "--format",
        default=default,
        choices=tabulate.tabulate_formats,
        help="Format of tabular output.")


class Table(markup.Table):
    def __init__(self, args, *cols, **kw):
        kw.setdefault('tablefmt', args.format)
        super().__init__(*cols, **kw)


class PathType(object):
    """
    A type to parse `pathlib.Path` instances from the command line.

    Similar to `argparse.FileType`.
    """
    def __init__(self, must_exist=True, type=None):
        assert type in (None, 'dir', 'file')
        self._must_exist = must_exist
        self._type = type

    def __call__(self, string):
        p = pathlib.Path(string)
        if self._must_exist and not p.exists():
            raise argparse.ArgumentTypeError('Path {0} does not exist!'.format(string))
        if p.exists() and self._type and not getattr(p, 'is_' + self._type)():
            raise argparse.ArgumentTypeError('Path {0} is not a {1}!'.format(string, self._type))
        return p
