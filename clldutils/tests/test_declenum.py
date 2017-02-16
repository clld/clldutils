# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase


class Tests(TestCase):
    def test_DeclEnum(self):
        from clldutils.declenum import DeclEnum

        class A(DeclEnum):
            val1 = '1', 'value 1'
            val2 = '2', 'value 2'

        for val, desc in A:
            self.assertEqual(val, '1')
            break

        self.assertEqual(len(A.values()), 2)
        self.assertIn('1', repr(A.val1))
        self.assertEqual(A.from_string('1'), A.val1)
        with self.assertRaises(ValueError):
            A.from_string('x')
        assert A.val1.__json__() == A.val1.__unicode__()
