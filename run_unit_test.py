import unittest
from utils.logger import Logger
from unit_tests.test import Test
from unit_tests.utils.test_config import TestConfig
from unit_tests.utils.test_metadata import TestMetadata
from unit_tests.utils.variables.test_variable_builder import TestVariableBuilder
import sys

test_classes = [Test,TestConfig,TestMetadata,TestVariableBuilder]

Logger.debug(False)
Logger.warning(False)
Logger.info(False)
Logger.error(False)

loader = unittest.TestLoader()
tests = [
    loader.loadTestsFromTestCase(test)
    for test in test_classes
]
suite = unittest.TestSuite(tests)

runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)

sys.exit(0 if res.wasSuccessful() else 1)