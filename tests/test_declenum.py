import pytest

from clldutils.declenum import DeclEnum


def test_DeclEnum_int():
    class A(DeclEnum):
        val1 = 2, 'x'
        val2 = 3, 'y'
        val3 = 1, 'z'

    assert A.val1.name == 'val1'
    assert '{0}'.format(A.val1) == '2'
    assert A.val1 > A.val3
    assert A.val2 > A.val1
    assert A.val1 == A.get(A.val1)
    assert A.val1 == A.get(2)
    assert A.get(1) < A.get(3)

    with pytest.raises(ValueError):
        A.get(5)

    d = {v: v.description for v in A}
    assert sorted(d)[0] == A.val3


def test_DeclEnum():
    class A(DeclEnum):
        val1 = '1', 'value 1'
        val2 = '2', 'value 2'

    for val, desc in A:
        assert val == '1'
        break

    assert len(list(A.values())) == 2
    assert '1' in repr(A.val1)
    assert A.from_string('1') == A.val1
    with pytest.raises(ValueError):
        A.from_string('x')
    assert A.val1.__json__(None) == str(A.val1)
