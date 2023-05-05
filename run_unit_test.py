import unittest
from unit_tests.test import Test
import sys

test_classes = [Test]


loader = unittest.TestLoader()
tests = [
    loader.loadTestsFromTestCase(test)
    for test in (Test,)
]
suite = unittest.TestSuite(tests)

runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)

sys.exit(0 if res.wasSuccessful() else 1)