import unittest

from utils.logger import Logger
from utils.config import *

class TestConfig(unittest.TestCase):
    
    def test_join_success(self):
        parts = ["{id}","climate","{id}a.pccl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc"] 
        fd = FileRegex(file_parts=parts)
        dir =  "climatearchive_sample_data/data"
        res = fd.join(dir,"texpa1")
        self.assertEqual(len(res),12)
        self.assertIn("climatearchive_sample_data/data/texpa1/climate/texpa1a.pccljan.nc",res)
        
    def test_build_success(self):
        assert(type(FileDescriptor.build("/texpa1/climate/texpa1a.pccljan.nc")) is FileDescriptor)
        assert(type(FileDescriptor.build("{regex}/texpa1/climate/texpa1a.pccljan.nc")) is FileRegex)
        assert(type(FileDescriptor.build(["/texpa1/climate/texpa1a.pccljan.nc","/texpa1/climate/texpa1a.pcclfeb.nc"])) is FileSum)

        
    def test_assert_key_value_success(self):
        assert(HyperParametersConfig.assert_key_value("Atmosphere",{"levels":[1,2],"unit":"m","resolutions":[(1.0,2.0)]}))
        
        assert(HyperParametersConfig.assert_key_value("Ocean",{"levels":[1,2],"unit":"m","resolutions":[(1.0,2.0)]}))
        
    def test_assert_key_value_failure(self):
        assert(not HyperParametersConfig.assert_key_value("Atmosphere",{"levels":[1,2],"unit":"m","resolutions":[(1.0,2.0,3.0)]}))
        assert(not HyperParametersConfig.assert_key_value("Atmosphere",{"levels":[1,2],"fvzfv":"m"}))
        assert(not HyperParametersConfig.assert_key_value("Atmosphere",{"fvbfbx":[1,2],"unit":"m","resolutions":[(1.0,2.0)]}))
        assert(not HyperParametersConfig.assert_key_value("Atmosphere",{"levels":[1,"Csdc"],"unit":"m","resolutions":[(1.0,2.0)]}))
        
        assert(not HyperParametersConfig.assert_key_value("Ocean",{"levels":[1,2],"unit":"m","resolutions":[(1.0,2.0,3.0)]}))
        assert(not HyperParametersConfig.assert_key_value("Ocean",{"levels":[1,2],"fvzfv":"m"}))
        assert(not HyperParametersConfig.assert_key_value("Ocean",{"fvbfbx":[1,2],"unit":"m","resolutions":[(1.0,2.0)]}))
        assert(not HyperParametersConfig.assert_key_value("Ocean",{"levels":[1,"Csdc"],"unit":"m","resolutions":[(1.0,2.0)]}))
        
    def test_map_key_value_success(self):
        assert("resolutions" in HyperParametersConfig.map_key_value("Atmosphere",{}))
        
    def test_HyperParametersConfigb_bind_success(self):
        old = HyperParametersConfig(preprocessing="OLD")
        new = HyperParametersConfig.bind(old)
        assert(new.preprocessing == "OLD")
        
    def test_HyperParametersConfig_extends_success(self):
        old = HyperParametersConfig(preprocessing="OLD")
        old.extends(preprocessing = "NEW")
        old.extends(processing = "NEW")
        assert(old.preprocessing == "NEW")
        assert(old.processing == "NEW")
        
    def test_HyperParametersConfig_build_success(self):
        hp = HyperParametersConfig.build(preprocessing = "NEW")
        assert(hp.preprocessing == "NEW")
        
    def test_get_hp_success(self):
        hp = HyperParametersConfig.build(preprocessing = "NEW")
        config = Config(name="",
            supported_variables=
                {"var":VariableDescription(name="var",nc_file_var_binder=[],hyper_parameters=hp)},
            hyper_parameters=hp,id_metadata=None)
        assert(config.get_hp("var").preprocessing == "NEW")
        
    def test_get_realm_hp_success(self):
        @dataclass
        class MockVariable:
            name:str
            realm:str
        hp = HyperParametersConfig.build(preprocessing = "NEW")
        config = Config(name="",
            supported_variables=
                {"var":VariableDescription(name="var",nc_file_var_binder=[],hyper_parameters=hp)},
            hyper_parameters=hp,id_metadata=None)
        assert("levels" in config.get_realm_hp(MockVariable(name="var",realm="a")))
        assert("unit" in config.get_realm_hp(MockVariable(name="var",realm="a")))
        assert("resolutions" in config.get_realm_hp(MockVariable(name="var",realm="a")))
        assert("resolutions" in config.get_realm_hp(MockVariable(name="var",realm=None)))
        
    def test_look_up_success(self):   
        @dataclass(frozen=True,eq=True)
        class MockVariable:
            name:str
            realm:str     
        hp = HyperParametersConfig.build(preprocessing = "NEW")
        config = Config(name="",
            supported_variables=
                {"var":VariableDescription(name="var",nc_file_var_binder=[(FileDescriptor.build(["/{id}/climate/{id}a.pccljan.nc","{id}/climate/{id}a.pcclfeb.nc"]),"varname",False)],hyper_parameters=hp)},
            hyper_parameters=hp,id_metadata=None)
        mock_variable = MockVariable(name="var",realm=None)
        res = (list(config.look_up(input_folder="climatearchive_sample_data/data",
                                   id="texpa1",
                                   variable=mock_variable)))

        assert(len(res) == 1)
        file_paths,var_name = res[0]
        assert(len(file_paths) == 2)
        assert(var_name == "varname")
        
        