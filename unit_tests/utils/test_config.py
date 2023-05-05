import unittest

from utils.logger import Logger
from utils.config import *

class TestConfig(unittest.TestCase):
    
    def test_join_success(self):
        parts = ["{id}","climate","{id}a.pccl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc"] 
        fd = FileDescriptor(file_parts=parts)
        dir =  "climatearchive_sample_data/data"
        res = fd.join(dir,"texpa1")
        self.assertEqual(len(res),12)
        self.assertEqual(res[1],"climatearchive_sample_data/data/texpa1/climate/texpa1a.pccljan.nc")
        
    def test_build_success(self):
        assert(False)
        
    def test_assert_key_value_success(self):
        assert(False)
        
    def test_map_key_value_success(self):
        assert(False)
        
    def test_HyperParametersConfigb_bind_success(self):
        assert(False)
        
    def test_HyperParametersConfig_extends_success(self):
        assert(False)
        
    def test_HyperParametersConfig_build_success(self):
        assert(False)
        
    def test_get_hp_success(self):
        assert(False)
        
    def test_get_realm_hp_success(self):
        assert(False)
        
    def test_look_up_success(self):
        assert(False)
        
    def test_Config_build_success(self):
        assert(False)
        