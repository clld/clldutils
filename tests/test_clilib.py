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
        _, sp = get_parser_and_subparsers('a')
        res = register_subcommands(sp, pkg, entry_point='x')
        assert 'cmd' in res
        assert 'abc.cmd' in res


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
