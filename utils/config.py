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
    Atmosphere : dict = field(default_factory=lambda: {'levels':[1000, 850, 700, 500, 200, 100, 10],'unit':'hPa'}) 
    Ocean : dict = field(default_factory=lambda: {'levels':[0, 100, 200, 500, 1000, 2000, 4000],'unit':'m'})
    resolutions : list =  field(default_factory=lambda: [(None,None)])
    
    
    @staticmethod
    def assert_key_value(key,value) -> bool:
        if key == "resolutions":
            if all(len(r) == 2 for r in  value):
                return True
            else :
                Logger.console().warning(f"can't convert resolutions to tuples, set to default {HyperParametersConfig().resolutions} instead")
                return False
        return True
    
    @staticmethod
    def map_key_value(key,value) ->  Any:
        if key == "resolutions":
            new_res = [(r1, r2) if r1!= "default" and r2 != "default" else (None, None) for r1, r2 in value]
            return new_res
        return None
    
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
                    self.__dict__[key] = types[key].__call__(value)
    @staticmethod
    def build(**kwargs) -> 'HyperParametersConfig':
        hp = HyperParametersConfig()
        types = hp.__annotations__
        for key,value in kwargs.items():
            if key in hp.__dict__ and HyperParametersConfig.assert_key_value(key,value):
                if type(value) is types[key]:
                    hp.__dict__[key] = types[key].__call__(value)
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
    

    def look_up(self,input_folder:str,id:str,variables:list) -> Generator[Tuple[Union[str,List[str]],str,Any], None, None]:
        
        directory = input_folder if input_folder != self.directory else self.directory
        
        for variable in variables:
            if variable.name in self.supported_variables:
                supported_variable = self.supported_variables[variable.name]
                for file_desc,var_name in supported_variable.nc_file_var_binder:
                    if type(file_desc) is FileDescriptor:
                        file_paths = file_desc.join(directory,id)
                        if all(path.isfile(file_path) for file_path in file_paths):
                            yield file_paths,var_name,variable
                    if type(file_desc) is FileSum:
                        file_paths = []
                        print(file_desc.files)
                        for file in file_desc.files:
                            file_paths.extend(file.join(directory,id))
                        print(file_paths)
                        if all(path.isfile(file_path) for file_path in file_paths):
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