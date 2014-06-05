"""
Makes sure that the smallwm.structs.Struct metaclass works as expected.
"""
import os
import sys
import unittest

# Ensure we can import smallwm
sys.path.append(os.path.join(*os.path.split(sys.path[0])[:-1]))

from smallwm.structs import Struct

class SimpleStruct(metaclass=Struct):
    __slots__ = 'a', 'b', 'c'

class ComplexStruct(metaclass=Struct):
    __slots__ = 'a', 'b', 'c'
    __defaults__ = {'b': -1, 'c': -2}

class JustSlotsTest(unittest.TestCase):
    """
    Tests with a Struct that uses only __slots__.
    """
    def test_correct_usage(self):
        """
        Ensures that correct usages sets the attributes.
        """
        x = SimpleStruct(1, 2, 3)
        self.assertEqual(x.a, 1)
        self.assertEqual(x.b, 2)
        self.assertEqual(x.c, 3)

    def test_incorrect_usage(self):
        """
        Ensures that the wrong number of arguments throws a TypeError.
        """
        # Too many arguments
        with self.assertRaises(TypeError):
             SimpleStruct(1, 2, 3, 4)

        # Too few arguments
        with self.assertRaises(TypeError):
            SimpleStruct(1, 2)

class WithDefaultsTest(unittest.TestCase):
    """
    Tests with a Struct that uses __defaults__.
    """
    def test_correct_usage(self):
        """
        Ensures that correct usage sets the proper attributes:

         - Allows only non-default attributes to be set
         - Allows for default attributes to be overridden
        """
        x = ComplexStruct(a=1)
        self.assertEqual(x.a, 1)
        self.assertEqual(x.b, -1)
        self.assertEqual(x.c, -2)

        y = ComplexStruct(a=1, b=2)
        self.assertEqual(y.a, 1)
        self.assertEqual(y.b, 2)
        self.assertEqual(y.c, -2)

    def test_incorrect_usage(self):
        """
        Ensures that incorrect usage throws a TypeError:

         - Non-set non-default attributes are errors
        """
        with self.assertRaises(TypeError):
            x = ComplexStruct()

if __name__ == '__main__':
    unittest.main()
