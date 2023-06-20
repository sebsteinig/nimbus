import unittest
from unit_tests.utils.test_metadata import TestMetadata
from unit_tests.utils.variables.pipelines.test_cleaning_pipelines import TestCleaningPipeLine
from utils.logger import Logger
from unit_tests.test import Test
from unit_tests.utils.test_config import TestConfig
from unit_tests.utils.test_metadata import TestMetadata
from unit_tests.utils.variables.test_variable_builder import TestVariableBuilder
from unit_tests.supported_variables.utils.test_supported_variable import TestSupportedVariable
from unit_tests.utils.variables.pipelines.test_horizontal_pipelines import TestHorizontalPipeLine
from unit_tests.utils.variables.pipelines.test_vertical_pipelines import TestVerticalPipeLine
from unit_tests.utils.variables.test_info import TestInfo
import sys

test_classes = [
    Test,
    TestConfig,
    TestMetadata,
    TestVariableBuilder,
    TestSupportedVariable,
    TestHorizontalPipeLine,
    TestVerticalPipeLine,
    TestCleaningPipeLine,
    TestInfo
]

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