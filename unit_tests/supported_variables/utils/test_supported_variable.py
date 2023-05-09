import unittest

from supported_variables.utils.supported_variable import *

class TestSupportedVariable(unittest.TestCase):
    
    def test_preprocessing_success(self):
        @supported_variable
        class Test:pass
        
        @preprocessing(Test,"TEST")        
        def preprocess():
            return True
        
        assert("test" in Test.preprocess_functions)
        assert(Test.preprocess_functions["test"]())
        
    
    def test_processing_success(self):
        @supported_variable
        class Test:pass
        
        @processing(Test,"TEST")        
        def process():
            return True
        
        assert("test" in Test.process_functions)
        assert(Test.process_functions["test"]())
        
    def test_supported_variable_success(self):
        @supported_variable
        class Test:pass
        
        assert("preprocess_functions" in Test.__dict__)
        assert("process_functions" in Test.__dict__)
        assert("realm" in Test.__dict__)
        assert(Test.preprocess_functions is not None and type(Test.preprocess_functions) is dict)
        assert(Test.process_functions is not None and type(Test.process_functions) is dict)