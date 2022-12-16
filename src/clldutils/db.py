"""
This module provides tools to create/drop and use databases specified by DB URL. This module only
handles SQLite and PostgreSQL, but abstracts the differences between the two.
"""
import typing
import logging
import pathlib
import sqlite3
import subprocess
import urllib.parse

from clldutils.path import ensure_cmd

__all__ = ['DB', 'TempDB', 'FreshDB']

CREATEDB = 'createdb'
DROPDB = 'dropdb'
PSQL = 'psql'


class DB:
    """
    A relational database specified by DB URL. Supported dialects are "sqlite" and "postgresql".

    .. seealso::

        `<https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine>`_
    """
    settings_key = 'sqlalchemy.url'

    def __init__(self, url: str, log: typing.Optional[logging.Logger] = None):
        self.log = log
        self.components = urllib.parse.urlparse(url)
        if self.dialect not in ['sqlite', 'postgresql']:
            raise NotImplementedError(self.dialect)
        if self.dialect == 'postgresql':
            assert all(bool(ensure_cmd(cmd)) for cmd in [CREATEDB, DROPDB, PSQL])

    def __str__(self):
        return self.components.geturl()

    @classmethod
    def from_settings(cls, settings: dict, log=None):
        """
        Instantiate a DB looking up the URL in a `dict`.

        :param settings: A `dict` as returned - e.g. - by `pyramid.paster.get_appsettings`.
        """
        return cls(settings[cls.settings_key], log=log)

    @property
    def dialect(self) -> str:
        return str(self.components.scheme.split('+')[0])

    @property
    def name(self):
        assert self.components.path.startswith('/')
        return self.components.path[1:].split('?')[0]

    def exists(self) -> bool:
        """
        Does the database exist?
        """
        if self.dialect == 'postgresql':
            dbs = [
                line.split('|')[0].strip() for line in
                subprocess.check_output([PSQL, '-lqt']).decode('utf8').splitlines()]
            return self.name in dbs
        return pathlib.Path(self.name).exists()

    def create(self):
        """
        Create the database

        :raises ValueError: If the database already exists.
        """
        if self.log:
            self.log.info('creating {0}'.format(self))
        if self.dialect == 'postgresql':
            subprocess.check_call([CREATEDB, self.name])
        else:  # self.dialect == 'sqlite'
            if self.exists():
                raise ValueError('db exists!')
            sqlite3.connect(self.name)

    def drop(self):
        """
        Drop the database or remove the db file for sqlite.
        """
        if self.exists():
            if self.log:
                self.log.info('dropping {0}'.format(self))
            if self.dialect == 'postgresql':
                subprocess.check_call([DROPDB, self.name])
            else:
                pathlib.Path(self.name).unlink()


class FreshDB(DB):
    """
    Context manager to use a newly created database.

    .. code-block:: python

        >>> with FreshDB(url) as db:
        ...     assert db.exists()
    """
    def __enter__(self):
        self.drop()
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TempDB(DB):
    """
    Context manager to use a temporary database.

    .. code-block::

        >>> with TempDB(url) as db:
        ...     assert db.exists()
        >>> assert not db.exists()
    """
    def __enter__(self):
        assert not self.exists()
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.drop()
