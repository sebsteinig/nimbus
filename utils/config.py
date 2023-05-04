from dataclasses import dataclass, field
import os.path as path
from pathlib import PurePath,Path
from typing import Any, Dict, Generator, List, Tuple, Union
import tomli
if __name__ == "__main__":
    from logger import Logger,_Logger
else :
    from utils.logger import Logger,_Logger
import re

class ConfigException(Exception):pass

@dataclass
class FileSum:
    files : List['FileDescriptor']
    
@dataclass
class FileDescriptor:
    #file_parts : List[str]
    file : str
    def join(self,dir:str,id:str) -> List[str]:
        dir_path = Path(dir)
        regex = self.file.replace("{id}",id)
        return [str(f) for f in dir_path.glob("**/*") if re.search(regex, str(f))]
    
    @staticmethod
    def build(files:Union[str,List[str]]) -> Union['FileDescriptor',FileSum]:
        if type(files) is str:
            return FileDescriptor(file=files)
        if type(files) is list:
            return FileSum(files=[FileDescriptor.build(file) for file in files])
@dataclass
class HyperParametersConfig:
    preprocessing : str = 'default'
    processing : str = 'default'
    realm : str = None
    threshold : float = 0.95
    Atmosphere : dict = field(default_factory=lambda: {'levels':[1000, 850, 700, 500, 200, 100, 10],'unit':'hPa','resolutions':[(None,None)]}) 
    Ocean : dict = field(default_factory=lambda: {'levels':[0, 100, 200, 500, 1000, 2000, 4000],'unit':'m','resolutions':[(None,None)]})
    
    
    @staticmethod
    def assert_key_value(key,value) -> bool:
        if key == "Atmosphere" or key == "Ocean":
            if "levels" in value:
                if type(value["levels"]) is not list :
                    Logger.console().warning("levels must be a list")
                    return False
                if not all(type(v) is float or type(v) is int for v in value['levels']):
                    Logger.console().warning("all values of levels must be integers or floats")
                    return False
            else :
                Logger.console().warning("levels is not present, set to default instead")
                return False
            if "unit" not in value:
                Logger.console().warning("unit is not present, set to default instead")
                return False
            if "resolutions" in value: 
                if all(len(r) == 2 for r in  value["resolutions"]):
                    return True
                else :
                    Logger.console().warning(f"can't convert resolutions to tuples, set to default instead")
                    return False
        return True

    @staticmethod
    def map_key_value(key,value) ->  Any:
        if key == "Atmosphere" or key == "Ocean":
            if "resolutions" in value:
                value["resolutions"] = [(None if r1 == "default" else r1, None if r2 == "default" else r2) for r1, r2 in value["resolutions"]]
            else :
                value["resolutions"] = [(None,None)]
        return value
    
    @staticmethod
    def bind(config:'HyperParametersConfig') -> 'HyperParametersConfig':
        hp = HyperParametersConfig()
        for key,value in config.__dict__.items():
            hp.__dict__[key] = value
        return hp
    
    def extends(self,**kargs):
        types = self.__annotations__
        for key,value in kargs.items():
            if key in self.__dict__ and HyperParametersConfig.assert_key_value(key,value):
                if type(value) is types[key]:
                    self.__dict__[key] = HyperParametersConfig.map_key_value(key,types[key].__call__(value))

    @staticmethod
    def build(**kwargs) -> 'HyperParametersConfig':
        hp = HyperParametersConfig()
        types = hp.__annotations__
        for key,value in kwargs.items():
            if key in hp.__dict__ and HyperParametersConfig.assert_key_value(key,value):
                if type(value) is types[key]:
                    hp.__dict__[key] = HyperParametersConfig.map_key_value(key,types[key].__call__(value))
        return hp
        
@dataclass
class VariableDescription:
    name : str
    nc_file_var_binder : List[Tuple[Union[FileDescriptor,FileSum],str]]
    hyper_parameters : HyperParametersConfig
    

    @staticmethod
    def build(var_desc:dict,name:str,hyper_parameters_config:HyperParametersConfig) -> 'VariableDescription':
        nc_file_var_binder = []
        hyper_parameters = HyperParametersConfig.bind(hyper_parameters_config)
        hyper_parameters.extends(**var_desc)
        for file_var in var_desc["variables"]:
            if "files" not in file_var and "variable" not in file_var:
                raise ConfigException(f"must be a dict with a file and a variable key")
            
            
            files = file_var["files"]
            variable = file_var["variable"]
            if type(variable) is not str or variable is None or variable == "":
                raise ConfigException(f" must have a non empty string variable")
            
            nc_file_var_binder.append((FileDescriptor.build(files),variable))
        
        return VariableDescription(name=name,\
            nc_file_var_binder=nc_file_var_binder,\
            hyper_parameters=hyper_parameters)
        
@dataclass
class Config:
    directory : str
    name : str
    supported_variables : Dict[str,VariableDescription]
    hyper_parameters : HyperParametersConfig

    def get_hp(self,var_name) -> HyperParametersConfig:
        if var_name in self.supported_variables:
            return self.supported_variables[var_name].hyper_parameters
        return self.hyper_parameters
    
    def get_realm_hp(self,variable) -> dict:
        if variable.realm is None:
            return {"resolutions":[(None,None)]}
            
        if variable.realm.lower() == "a" or variable.realm.lower() == "atmosphere":
            return self.supported_variables[variable.name].hyper_parameters.Atmosphere
        elif variable.realm is not None and (variable.realm.lower() == "o" or variable.realm.lower() == "ocean"):
            return self.supported_variables[variable.name].hyper_parameters.Ocean
        else :
            return {"resolutions":[(None,None)]}
    

    def look_up(self,input_folder:str,id:str,variables:list) -> Generator[Tuple[Union[str,List[str]],str,Any], None, None]:
        
        directory = input_folder if input_folder != self.directory else self.directory
        
        for variable in variables:
            if variable.name in self.supported_variables:
                supported_variable = self.supported_variables[variable.name]
                for file_desc,var_name in supported_variable.nc_file_var_binder:
                    if type(file_desc) is FileDescriptor:
                        file_paths = file_desc.join(directory,id)
                        if len(file_paths) != 0 and all(path.isfile(file_path) for file_path in file_paths):
                            yield file_paths,var_name,variable
                    if type(file_desc) is FileSum:
                        file_paths = []
                        for file in file_desc.files:
                            file_paths.extend(file.join(directory,id))
                        if len(file_paths) != 0 and all(path.isfile(file_path) for file_path in file_paths):
                            yield file_paths,var_name,variable
    
    @staticmethod
    def build(desc:str) -> 'Config':
        if not path.isfile(desc) and path.basename(desc).split('.')[-1] == "toml":
            raise ConfigException(f"{desc} is not a valid toml file")
        with open(desc,mode="rb") as fp:
            config = tomli.load(fp)
        
        if "Model" not in config :
            raise ConfigException(f"{desc} is not a valid config file, please provide a Model tag")
        model = config["Model"]
        if "dir" not in model:
            raise ConfigException(f"{desc} is not a valid config file, please provide a directory in the Model tag")
        directory = model["dir"]
        if "name" not in model:
            raise ConfigException(f"{desc} is not a valid config file, please provide a name in the Model tag")
        name = model["name"]
        
        hyper_parameters = HyperParametersConfig.build(**model)
        
        supported_variable = {}
        
        for var_name,var_desc in config.items():
            if var_name == "Model":
                continue
            supported_variable[var_name] = VariableDescription.build(var_desc=var_desc,name = var_name,hyper_parameters_config = hyper_parameters)
            
        return Config(directory=directory,name=name,supported_variables=supported_variable,hyper_parameters=hyper_parameters)


def glob_re(path, regex="", glob_mask="**/*", inverse=False):
    p = Path(path)
    if inverse:
        res = [str(f) for f in p.glob(glob_mask) if not re.search(regex, str(f))]
    else:
        res = [str(f) for f in p.glob(glob_mask) if re.search(regex, str(f))]
    return res
    
if __name__ == "__main__":
    
    print(glob_re("/home/willem/workspace/internship-climate-archive/climatearchive_sample_data/data/","(texpa1|texqd)/.*ann.nc"))
    
    """
    config = Config.build("BRIDGE.toml")
    
    print(config)
    
    for name,var_desc in config.supported_variables.items():
        print(name)
        for file_desc,var_name in var_desc.nc_file_var_binder:
            if type(file_desc) is FileDescriptor:
                print(file_desc.join("texpa1"))
    """