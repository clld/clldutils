# coding: utf8
from __future__ import unicode_literals, print_function, division

import pytest

try:
    import pathlib2 as pathlib
except ImportError:  # pragma: no cover
    import pathlib

from clldutils import dsv


@pytest.fixture
def tmppath(tmpdir):
    return pathlib.Path(str(tmpdir))
