import pathlib

import pytest


@pytest.fixture
def tmppath(tmpdir):
    return pathlib.Path(str(tmpdir))
