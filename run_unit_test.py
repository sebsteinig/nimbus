import unittest
from unit_tests.utils.test_metadata import TestMetadata
from unit_tests.utils.test_png_converter import TestPngConverter
from unit_tests.test import Test
import sys

test_classes = [Test, TestMetadata, TestPngConverter]


loader = unittest.TestLoader()
tests = [
    loader.loadTestsFromTestCase(test)
    for test in (test_classes)
]
suite = unittest.TestSuite(tests)

runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)

sys.exit(0 if res.wasSuccessful() else 1)