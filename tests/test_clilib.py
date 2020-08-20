import pathlib
import argparse
import importlib

import pytest

from clldutils.clilib import *
from clldutils.path import sys_path


def test_get_parser_and_subparser():
    assert get_parser_and_subparsers('a')


def test_register_subcommands(fixtures_dir, mocker):
    with sys_path(fixtures_dir):
        pkg = importlib.import_module('commands')
        class EP:
            name = 'abc'
            def load(self):
                return pkg
        mocker.patch(
            'clldutils.clilib.pkg_resources',
            mocker.Mock(iter_entry_points=mocker.Mock(return_value=[EP()])))
        parser, sp = get_parser_and_subparsers('a')
        res = register_subcommands(sp, pkg, entry_point='x')
        assert 'cmd' in res
        assert 'abc.cmd' in res

        help = None
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                if choice == 'cmd':
                    help = subparser.format_help()
        # Make sure a RawDescription formatter is used:
        assert 'Test command\n- formatted' in help
        # Make sure default values are formatted:
        assert 'o (default: x)' in help

        res = register_subcommands(sp, pkg, formatter_class=argparse.HelpFormatter)
        help = None
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                if choice == 'cmd':
                    help = subparser.format_help()
        # Make sure a RawDescription formatter is used:
        assert 'Test command\n- formatted' not in help
        # Make sure default values are formatted:
        assert 'o (default: x)' not in help

def test_register_subcommands_error(fixtures_dir, mocker, recwarn):
    with sys_path(fixtures_dir):
        pkg = importlib.import_module('commands')
        pkg_problematic = importlib.import_module('problematic_commands')
        class EP:
            name = 'abc'
            def load(self):
                raise ImportError()
        mocker.patch(
            'clldutils.clilib.pkg_resources',
            mocker.Mock(iter_entry_points=mocker.Mock(return_value=[EP()])))
        _, sp = get_parser_and_subparsers('a')
        with pytest.raises(ValueError):
            _ = register_subcommands(sp, pkg_problematic, entry_point='x')
        res = register_subcommands(sp, pkg, entry_point='x')
        assert 'abc.cmd' not in res
        assert recwarn.pop(UserWarning)


def test_ArgumentParser(capsys):
    def cmd(args):
        """
        docstring
        """
        if len(args.args) < 1:
            raise ParserError('not enough arguments')
        print(args.args[0])

    parser = ArgumentParserWithLogging('pkg', cmd)

    parser.main(args=['help', 'cmd'])
    out, err = capsys.readouterr()
    assert 'docstring' in out

    parser.main(args=['cmd', 'arg'])
    out, err = capsys.readouterr()
    assert 'arg' in out

    assert parser.main(args=['cmd', 'arg']) == 0

    parser.main(args=['cmd'])
    out, err = capsys.readouterr()
    assert 'not enough arguments' in out

    assert parser.main(args=['x']) != 0
    out, err = capsys.readouterr()
    assert out.startswith('invalid')

    @command()
    def ls(args):
        """
        my name is ls
        """
        return

    @command(name='list', usage='my name is {0}'.format('list'))
    def f(args):
        """
        """
        return

    parser = ArgumentParserWithLogging('pkg')
    parser.main(args=['help', 'ls'])
    out, err = capsys.readouterr()
    assert 'my name is ls' in out

    parser.main(args=['help', 'list'])
    out, err = capsys.readouterr()
    assert 'my name is list' in out

    assert parser.main(args=['ls', 'arg']) == 0
    assert parser.main(args=['list', 'arg']) == 0


def test_cmd_error():
    from clldutils.clilib import ArgumentParser

    def cmd(args):
        raise ValueError

    parser = ArgumentParser('pkg', cmd)
    with pytest.raises(ValueError):
        parser.main(args=['cmd'])

    assert parser.main(args=['cmd'], catch_all=True) == 1


def test_confirm(capsys, mocker):
    from clldutils.clilib import confirm

    mocker.patch('clldutils.clilib.input', mocker.Mock(return_value=''))
    assert confirm('a?')
    assert not confirm('a?', default=False)

    mocker.patch('clldutils.clilib.input', mocker.Mock(side_effect=['x', 'y']))
    assert confirm('a?')
    out, err = capsys.readouterr()
    assert 'Please respond' in out


def test_Table(capsys):
    with Table(argparse.Namespace(format='simple'), 'a') as t:
        t.append(['x'])
    out, _ = capsys.readouterr()
    assert out == 'a\n---\nx\n'


def test_add_format():
    parser, _ = get_parser_and_subparsers('c')
    add_format(parser)


def test_PathType(tmpdir):
    parser = argparse.ArgumentParser()
    parser.add_argument('a', type=PathType(type='file'))
    args = parser.parse_args([__file__])
    assert isinstance(args.a, pathlib.Path)

    with pytest.raises(SystemExit):
        parser.parse_args(['x'])

    with pytest.raises(SystemExit):
        parser.parse_args([str(tmpdir)])
