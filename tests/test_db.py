import pathlib
import logging

import pytest

from clldutils.db import *


@pytest.fixture
def sqliteurl(tmp_path):
    return 'sqlite:///{0}'.format(tmp_path / 'test.sqlite')


def test_DB_init():
    with pytest.raises(NotImplementedError):
        DB('http://example.org')
    assert DB('sqlite:////a').name == '/a'
    assert DB('sqlite+abc:////a').dialect == 'sqlite'
    assert DB('postgresql://a/a?k=v').name == 'a'


def test_DB_from_settings():
    assert DB.from_settings({'sqlalchemy.url': 'sqlite://example.org/p'}).name == 'p'


def test_sqlite(caplog, sqliteurl):
    db = DB(sqliteurl, log=logging.getLogger(__name__))
    assert not db.exists()
    with caplog.at_level(logging.INFO):
        db.create()
        assert 'sqlite' in str(caplog.records[-1])
    with pytest.raises(ValueError):
        db.create()
    assert db.exists()
    with caplog.at_level(logging.INFO):
        db.drop()
        assert 'drop' in str(caplog.records[-1]).lower()
    assert not db.exists()


def test_postgresql_invalid(mocker):
    mocker.patch('clldutils.db.ensure_cmd', mocker.Mock(side_effect=ValueError))

    with pytest.raises(ValueError):
        DB('postgresql://a@/b')


def test_postgresql(mocker):
    class subprocess:
        def check_output(self, *args, **kw):
            return """\
 csd                  | forkel | UTF8     | en_US.UTF-8 | en_US.UTF-8 | 
 dictionaria          | forkel | UTF8     | en_US.UTF-8 | en_US.UTF-8 | 
""".encode('utf8')

        def check_call(self, *args, **kw):
            pass

    mocker.patch('clldutils.db.subprocess', subprocess())
    db = DB('postgresql://a@/csd')
    assert db.exists()
    db.create()
    db.drop()


def test_context_managers(sqliteurl):
    with FreshDB(sqliteurl) as db:
        pass
    assert db.exists()

    with pytest.raises(AssertionError):
        with TempDB(sqliteurl):
            pass  # pragma: no cover

    pathlib.Path(db.name).unlink()
    with TempDB(sqliteurl) as db:
        assert db.exists()
    assert not db.exists()
