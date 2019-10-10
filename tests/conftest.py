import pathlib

import pytest


@pytest.fixture
def tmppath(tmpdir):
    return pathlib.Path(str(tmpdir))


@pytest.fixture
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'
