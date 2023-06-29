"""
This module provides functionality to make creation of CLI (command line interface) tools
easier.

In particular, we support the paradigm of one main command, providing access to subcommands, as
follows: In the main function of a CLI, e.g. the function exposed as `console_scripts` entry point,
you

- call :func:`clldutils.clilib.get_parser_and_subparsers`,
- add global options and arguments, and
- then pass the subparsers when calling :func:`clldutils.clilib.register_subcommands`,
- parse the command line
- and finally call `args.main` - which has been set to a subcommand's `run` function.

Subcommands must be implemented as Python modules with

- a docstring (describing the command)
- an optional `register(parser)` function, to register subcommand-specific arguments
- a `run(args: argparse.Namespace)` function, implementing the command functionality.

A fleshed-out usage example would look like this:

.. code-block:: python

    import mycli.commands

    def main():
        parser, subparsers = get_parser_and_subparsers('mycli')
        parser.add_argument(
            '-z', '--maxfieldsize',
            metavar='FIELD_SIZE_LIMIT',
            type=lambda s: csv.field_size_limit(int(s)),
            help='Maximum length of a single field in any input CSV file.',
            default=csv.field_size_limit(),
        )
        register_subcommands(subparsers, mycli.commands)

        args = parsed_args or parser.parse_args()

        if not hasattr(args, "main"):
            parser.print_help()
            return 1

        with contextlib.ExitStack() as stack:
            stack.enter_context(Logging(args.log, level=args.log_level))
            try:
                return args.main(args) or 0
            except KeyboardInterrupt:
                return 0
            except ParserError as e:
                print(e)
                return main([args._command, '-h'])

with subcommands impemented as modules in the `mycli.commands` package having the following
skeleton:

.. code-block:: python

    '''
    ... describe what the command does ...
    '''
    def register(parser):
        parser.add_argument('--flag')

    def run(args):
        if args.flag:
            pass
"""
import csv
import random
import typing
import logging
import pkgutil
import pathlib
import argparse
import warnings
import importlib
import collections
import importlib.metadata

import tabulate

from clldutils.loglib import Logging, get_colorlog
from clldutils.misc import deprecated
from clldutils import markup

__all__ = [
    'ParserError', 'Command', 'command', 'ArgumentParser', 'ArgumentParserWithLogging',
    'get_parser_and_subparsers', 'register_subcommands', 'PathType', 'add_format', 'Table',
    'add_csv_field_size_limit', 'add_random_seed', 'confirm',
]


def get_entrypoints(group):
    eps = importlib.metadata.entry_points()
    return eps.select(group=group) if hasattr(eps, 'select') else eps.get(group, [])


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
    def __init_subclass__(cls, **kwargs):
        if cls.__name__ != 'ArgumentParserWithLogging':
            deprecated(
                '{} inherits from clldutils.clilib.ArgumentParser which is deprecated.'.format(
                    cls.__name__
                ))
        super().__init_subclass__(**kwargs)

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


def confirm(question: str, default=True) -> bool:
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


def get_parser_and_subparsers(prog: str, with_defaults_help: bool = True, with_log: bool = True)\
        -> typing.Tuple[argparse.ArgumentParser, typing.Any]:
    """
    Get an `argparse.ArgumentParser` instance and associated subparsers.

    Wraps `argparse.ArgumentParser.add_subparsers`.

    :param prog: Name of the program, i.e. the main command.
    :param with_defaults_help: Whether defaults should be displayed in the help message.
    :param with_log: Whether a global option to select log levels should be available.
    """
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
    if hasattr(pkg, '__path__'):
        for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if not ispkg:
                modname = ".".join([pkg.__name__, name])
                try:
                    yield name, importlib.import_module(modname)
                except Exception as e:  # pragma: no cover
                    warnings.warn('{0} {1}'.format(e, modname))


def register_subcommands(
        subparsers,
        pkg: str,
        entry_point: typing.Optional[str] = None,
        formatter_class: argparse.ArgumentDefaultsHelpFormatter = Formatter,
        skip_invalid: bool = False):
    """
    Register subcommands discovered as modules in a Python package or via entry point.

    :param subparsers: An object as returned as second item by :func:`get_parser_and_subparsers`.
    :param pkg: A Python package in which to look for subcommands.
    :param entry_point: Name of an entry point group to use for looking up subcommands in other \
    installed packages.
    :param formatter_class: `argparse.ArgumentDefaultsHelpFormatter`'s subclass to use for help \
    formatting.
    """
    # Discover available commands:
    # Commands are identified by (<entry point name>).<module name>
    _cmds = collections.OrderedDict()
    _cmds.update(list(iter_modules(pkg)))
    if entry_point:
        # ... then look for commands provided in other packages:
        for ep in get_entrypoints(entry_point):
            try:
                pkg = ep.load()
            except ImportError:
                warnings.warn('ImportError loading entry point {0.name}'.format(ep))
                continue
            _cmds.update(
                [('.'.join([ep.name, name]), mod) for name, mod in iter_modules(pkg)])

    valid = collections.OrderedDict()
    for name, mod in _cmds.items():
        if not mod.__doc__:
            if skip_invalid:
                continue
            raise ValueError('Command \"{0}\" is missing a docstring.'.format(name))
        if not getattr(mod, 'run', None):  # pragma: no cover
            if skip_invalid:
                continue
            raise ValueError('Command \"{0}\" is missing a run function.'.format(name))

        valid[name] = mod
        subparser = subparsers.add_parser(
            name,
            help=mod.__doc__.strip().splitlines()[0] if mod.__doc__.strip() else '',
            description=mod.__doc__,
            formatter_class=formatter_class)
        if hasattr(mod, 'register'):
            mod.register(subparser)
        subparser.set_defaults(main=mod.run)

    return valid


def add_csv_field_size_limit(parser, default=None):
    """
    Command line tools reading CSV might run into problems with Python's
    `csv.field_size_limit <https://docs.python.org/3/library/csv.html#csv.field_size_limit>`_
    Adding this option to the cli allows users to override the default setting.

    Usage:

        .. code-block:: python

            def register(parser):
                add_csv_field_size_limit(parser)
    """
    parser.add_argument(
        '-z', '--maxfieldsize',
        metavar='FIELD_SIZE_LIMIT',
        type=lambda s: csv.field_size_limit(int(s)),
        help='Maximum length of a single field in any input CSV file.',
        default=csv.field_size_limit(default),
    )


def add_random_seed(parser, default: typing.Optional[int] = None):
    """
    Command line tools may want to fix Python's `random.seed` to ensure reproducible results.

    Usage:

        .. code-block:: python

            def register(parser):
                add_random_seed(parser, default=1234)
    """
    parser.add_argument(
        '--random-seed',
        type=lambda s: random.seed(int(s)),
        default=random.seed(default))


def add_format(parser, default: str = 'pipe'):
    """
    Add a `format` option, to be used with :class:`Table`.
    """
    parser.add_argument(
        "--format",
        default=default,
        choices=tabulate.tabulate_formats,
        help="Format of tabular output.")


class Table(markup.Table):
    """
    CLI tools outputting tabular data can use a `Table` object (optionally together with a cli
    option as in :func:`add_format`) to easily create configurable formats of tables.

    `Table` is a context manager which will print the formatted data to `stdout` at exit.

    .. code-block:: python

        def register(parser):
            add_format(parser, default='simple')

        def run(args):
            with Table(args, 'col1', 'col2') as t:
                t.append(['val1', 'val2'])

    .. note::

        With `--format=tsv` `Table` will output proper TSV, suitable for "piping" to CSV tools like
        the ones from `csvkit`.
    """
    def __init__(self, args: argparse.Namespace, *cols, **kw):
        kw.setdefault('tablefmt', args.format)
        super().__init__(*cols, **kw)


class PathType(object):
    """
    A type to parse `pathlib.Path` instances from the command line.

    Similar to `argparse.FileType`.

    Usage:

        .. code-block:: python

            def register(parser):
                parser.add_argument('input', type=PathType(type='file'))

            def run(args):
                assert args.input.exists()
    """
    def __init__(self, must_exist: bool = True, type: typing.Optional[str] = None):
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
