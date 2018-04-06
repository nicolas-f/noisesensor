import logging
import unittest
from cython_example_proj import factorial

"""
Some basic tests
"""

logging.basicConfig(level=logging.DEBUG)


class TestSTL(unittest.TestCase):

    def test_factorial(self):
        assert factorial(10) == 3628800

if __name__ == '__main__':
    unittest.main()
