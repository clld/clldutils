# coding: utf8
from __future__ import unicode_literals, print_function, division
from unittest import TestCase


class Tests(TestCase):
    def test_DeclEnum_int(self):
        from clldutils.declenum import DeclEnum

        class A(DeclEnum):
            val1 = 2, 'x'
            val2 = 3, 'y'
            val3 = 1, 'z'

        self.assertEqual(A.val1.name, 'val1')
        self.assertEqual('{0}'.format(A.val1), '2')
        self.assertGreater(A.val1, A.val3)
        self.assertGreater(A.val2, A.val1)
        self.assertEqual(A.val1, A.get(A.val1))
        self.assertEqual(A.val1, A.get(2))
        self.assertLess(A.get(1), A.get(3))

        with self.assertRaises(ValueError):
            A.get(5)

        d = {v: v.description for v in A}
        self.assertEqual(sorted(list(d.keys()))[0], A.val3)

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
        assert A.val1.__json__(None) == A.val1.__unicode__()
