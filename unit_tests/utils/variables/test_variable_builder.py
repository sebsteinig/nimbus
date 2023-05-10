import unittest

import supported_variables as supported_variables

import unit_tests.utils.mock_config as mock_config
from utils.variables.variable_builder import *

class TestVariableBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.supported_variables_names = ["clt","sic", 'currents', "height","liconc","mlotst","pfts","pr","snc","tas","tos","winds"]
        #,"oceanCurrents","siconc"
        self.config = mock_config.build()
        
        return super().setUp()
    
    def test_import_submodules_success(self):
        sub_modules = import_submodules(supported_variables.__name__)
        self.assertSetEqual(set(self.supported_variables_names),set(sub_modules.keys()))
        
    def test_build_success(self):
        variables = build(self.config)
        names = map(lambda v: v.name,variables)
        self.assertSetEqual(set(names),set(self.supported_variables_names))
        for variable in variables:
            assert(variable.preprocess is not None)
            assert(variable.process is not None)