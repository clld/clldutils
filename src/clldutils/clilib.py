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
from typing import Optional, Any
import logging
import pkgutil
import pathlib
import argparse
import warnings
import importlib
import importlib.metadata
import collections

from clldutils.loglib import get_colorlog
from clldutils import markup
from ._compat import entry_points_select

__all__ = [
    'ParserError',
    'get_parser_and_subparsers', 'register_subcommands', 'PathType', 'add_format', 'Table',
    'add_csv_field_size_limit', 'add_random_seed', 'confirm',
]


def get_entrypoints(group: str) -> list[importlib.metadata.EntryPoint]:
    """Returns entry points for a group."""
    eps = importlib.metadata.entry_points()
    return entry_points_select(eps, group=group)


class ParserError(Exception):
    """Exception to signal errors during cli input validation."""


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
    """Help formatter."""


def get_parser_and_subparsers(prog: str, with_defaults_help: bool = True, with_log: bool = True)\
        -> tuple[argparse.ArgumentParser, Any]:
    """
    Get an `argparse.ArgumentParser` instance and associated subparsers.

    Wraps `argparse.ArgumentParser.add_subparsers`.

    :param prog: Name of the program, i.e. the main command.
    :param with_defaults_help: Whether defaults should be displayed in the help message.
    :param with_log: Whether a global option to select log levels should be available.
    """
    kw = {'prog': prog}
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
                except Exception as e:  # pragma: no cover  # pylint: disable=W0718
                    warnings.warn(f'{e} {modname}')


def register_subcommands(
        subparsers,
        pkg: str,
        entry_point: Optional[str] = None,
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
                warnings.warn(f'ImportError loading entry point {ep.name}')
                continue
            _cmds.update(
                [('.'.join([ep.name, name]), mod) for name, mod in iter_modules(pkg)])

    valid = collections.OrderedDict()
    for name, mod in _cmds.items():
        if not mod.__doc__:
            if skip_invalid:
                continue
            raise ValueError(f'Command \"{name}\" is missing a docstring.')
        if not getattr(mod, 'run', None):  # pragma: no cover
            if skip_invalid:
                continue
            raise ValueError(f'Command \"{name}\" is missing a run function.')

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


def add_random_seed(parser, default: Optional[int] = None):
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
        default=markup.TableFormat.get(default),
        type=markup.TableFormat.get,
        # We can only use choices for validation. For the help message we must "abuse" metavar.
        # See https://docs.python.org/3/library/argparse.html#choices
        metavar=f'{{{",".join(e.name for e in markup.TableFormat)}}}',
        choices=markup.TableFormat,
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


class PathType:  # pylint: disable=R0903
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
    def __init__(
            self,
            must_exist: bool = True,
            type: Optional[str] = None):  # pylint: disable=W0622
        assert type in (None, 'dir', 'file')
        self._must_exist = must_exist
        self._type = type

    def __call__(self, string: str):
        p = pathlib.Path(string)
        if self._must_exist and not p.exists():
            raise argparse.ArgumentTypeError(f'Path {string} does not exist!')
        if p.exists() and self._type and not getattr(p, 'is_' + self._type)():
            raise argparse.ArgumentTypeError(f'Path {string} is not a {self._type}!')
        return p
