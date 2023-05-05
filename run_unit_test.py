import unittest
from unit_tests.test import Test
from unit_tests.utils.test_config import TestConfig
import sys

test_classes = [Test,TestConfig]


loader = unittest.TestLoader()
tests = [
    loader.loadTestsFromTestCase(test)
    for test in test_classes
]
suite = unittest.TestSuite(tests)

runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)

sys.exit(0 if res.wasSuccessful() else 1)