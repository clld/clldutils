# coding: utf8
from __future__ import unicode_literals, print_function, division

import pytest

from clldutils import dsv
from clldutils._compat import pathlib


@pytest.fixture
def tmppath(tmpdir):
    return pathlib.Path(str(tmpdir))
