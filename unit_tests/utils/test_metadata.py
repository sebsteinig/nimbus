import unittest
from utils.metadata import *
from unit_tests.utils.mock_metadata import MockMetadata

class TestMetadata(unittest.TestCase):
    data : MockMetadata
    
    def setUp(self) -> None:
        self.data = MockMetadata()
    
    def test_extends_specific_metadata_success(self):
        self.assertIsNone(self.data.var_s_2.original_xsize)
        self.data.var_s_2.extends(original_xsize = "1")
        self.assertEqual(self.data.var_s_2.original_xsize, "1")
        
    def test_extends_general_metadata_success(self):
        self.assertIsNone(self.data.var_g_2.yfirst)
        self.data.var_g_2.extends(yfirst = 3.4)
        self.assertEqual(self.data.var_g_2.yfirst, 3.4)
    
    def test_build_specific_metadata_success(self):
        self.data.var_s_3 = VariableSpecificMetadata.build(\
            original_variable_name = "name var1",\
               original_variable_long_name = "long name",\
               std_name = "std name 1",\
               model_name = "f",\
               min_max = [1, 2, 3])
        self.assertDictEqual(self.data.var_s_3.to_dict(),\
                             self.data.var_s_1.to_dict())

    def test_build_general_metadata_success(self):
        self.data.var_g_3 = GeneralMetadata.build(\
            variable_name = "name g 1",\
            xsize = 1,\
            ysize = 2,\
            xfirst = 4.5,\
            timesteps = 4,\
            created_at = "12nv2014",\
            threshold = 5)
        self.assertDictEqual(self.data.var_g_3.to_dict(),\
                             self.data.var_g_1.to_dict())

    def test_extends_inexistant_attribute_failure(self):
        self.data.var_s_1.extends(inexistant_attr = "value")
        with self.assertRaises(AttributeError):
            print(self.data.var_s_1.inexistant_attr)
    
    def test_build_inexistant_attribute_failure(self):
        self.data.var_g_1 = GeneralMetadata.build(inexistant_attr = "value")
        with self.assertRaises(AttributeError):
            print(self.data.var_g_1.inexistant_attr)
        
    def test_extends_metadata_success(self):
        self.data.metadata.general_metadata = self.data.var_g_2
        self.data.metadata.extends(xsize = 2)
        self.assertEqual(self.data.metadata.general_metadata.xsize, 2)
        
    def test_push_metadata_success(self):
        self.data.metadata.push([self.data.var_s_1, self.data.var_s_2])
        self.assertIn(self.data.var_s_1, self.data.metadata.vs_metadata)
        self.assertIn(self.data.var_s_2, self.data.metadata.vs_metadata)
        self.assertEqual(len(self.data.metadata.vs_metadata), 2)