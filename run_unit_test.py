import unittest
from unit_tests.test import Test
import sys

loader = unittest.TestLoader()
tests = [
    loader.loadTestsFromTestCase(test)
    for test in (Test,)
]
suite = unittest.TestSuite(tests)

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
sys.exit(1)