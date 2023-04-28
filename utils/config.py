from dataclasses import dataclass
import os.path as path
from pathlib import PurePath
from typing import Any, Dict, Generator, List, Tuple, Union
import tomli

class ConfigException(Exception):pass

@dataclass
class FileSum:
    files : List['FileDescriptor']
    
@dataclass
class FileDescriptor:
    file_parts : List[str]
    
    def join(self,id:str) -> str:
        return path.join(*(part.replace("{id}",id) for part in self.file_parts))
    
    @staticmethod
    def build(files:Union[str,List[str]]) -> Union['FileDescriptor',FileSum]:
        if type(files) is str:
            p_path = PurePath(files)
            return FileDescriptor(file_parts=p_path.parts)
        if type(files) is list:
            return FileSum(files=[FileDescriptor.build(file) for file in files])
        
@dataclass
class VariableDescription:
    name : str
    nc_file_var_binder : List[Tuple[Union[FileDescriptor,FileSum],str]]
    preprocessing : str = 'default'
    processing : str = 'default'
    
    @staticmethod
    def build(var_desc:dict,name:str) -> 'VariableDescription':
        nc_file_var_binder = []
        preprocessing = 'default' if "preprocessing" not in var_desc else var_desc["preprocessing"]
        processing = 'default' if "processing" not in var_desc else var_desc["processing"]
        
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
            preprocessing=preprocessing,\
            processing=processing)
    
@dataclass
class Config:
    directory : str
    name : str
    supported_variables : Dict[str,VariableDescription]
        

    def look_up(self,input_folder:str,id:str,variables:list) -> Generator[Tuple[Union[str,List[str]],str,Any], None, None]:
        
        directory = input_folder if input_folder != self.directory else self.directory
        
        for variable in variables:
            if variable.name in self.supported_variables:
                supported_variable = self.supported_variables[variable.name]
                for file_desc,var_name in supported_variable.nc_file_var_binder:
                    if type(file_desc) is FileDescriptor:
                        file_path = file_desc.join(id)
                        complete_file_path = path.join(directory,file_path)
                        if path.isfile(complete_file_path):
                            yield complete_file_path,var_name,variable
                    if type(file_desc) is FileSum:
                        file_paths = [file.join(id) for file in file_desc.files]
                        complete_file_paths = [path.join(directory,file_path) for file_path in file_paths]
                        if all(path.isfile(complete_file_path) for complete_file_path in complete_file_paths):
                            yield complete_file_paths,var_name,variable
    
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
        
        supported_variable = {}
        
        for var_name,var_desc in config.items():
            if var_name == "Model":
                continue
            supported_variable[var_name] = VariableDescription.build(var_desc=var_desc,name = var_name)
            
        return Config(directory=directory,name=name,supported_variables=supported_variable)
    
    
if __name__ == "__main__":
    config = Config.build("utils/test_config.toml")
    
    print(config)
    
    for name,var_desc in config.supported_variables.items():
        print(name)
        for file_desc,var_name in var_desc.nc_file_var_binder:
            if type(file_desc) is FileDescriptor:
                print(file_desc.join("texpa1"))