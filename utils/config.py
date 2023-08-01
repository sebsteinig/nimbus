from dataclasses import dataclass, field
import os.path as path
from os import scandir
import utils.metadata.parser as parser
from pathlib import PurePath,Path
from typing import Any, Dict, Generator, List, Tuple, Union
import numpy as np
import tomli

from utils.converters.utils.utils import Extension
if __name__ == "__main__":
    from logger import Logger,_Logger
else :
    from utils.logger import Logger,_Logger
import re

class ConfigException(Exception):pass

def memoize(f):
    cache = {}
    def memoized(dir_path,file_name):
        if file_name in cache:
            return cache[file_name]
        else :
            output = f(dir_path,file_name)
            cache[file_name] = output
            return output
    return memoized
        

@dataclass
class FileSum:
    files : List['FileDescriptor']
    """
        resolve file paths according to the given id and dir,
        first replace {id} flag by real id and regex match filename to retrieve
        correct file path
        param : 
            dir : str
            id : str
        return :
            List[str]
    """
    def join(self,dir:str,id:str) -> List[str]:
        file_paths = []
        for file in self.files:
            file_paths.append(file.join(dir,id))
        return file_paths
            
@dataclass
class FileRegex:
    file_parts : List[str]
    """
        resolve file paths according to the given id and dir,
        first replace {id} flag by real id and regex match filename to retrieve
        correct file path
        param : 
            dir : str
            id : str
        return :
            Set[str]
    """
    @memoize
    def regex_match(dir_path,file_name):
        if not path.isdir(dir_path):
            return {}
        regex = re.compile(file_name)
        return set(path.join(dir_path,f.name) for f in scandir(dir_path) if regex.match(f.name))
    
    def join(self,dir:str,id:str) -> List[str]:
        dir_path = path.join(dir,*(part.replace("{id}",id) for part in self.file_parts[:-1]))
        file_name = self.file_parts[-1].replace("{id}",id)
        
        return FileRegex.regex_match(dir_path,file_name)
    
@dataclass
class FileDescriptor:
    file_parts : List[str]
    
    """
        resolve file path according to the given id and dir,
        first replace {id} flag by real id
        correct file path
        param : 
            dir : str
            id : str
        return :
            str
    """
    def join(self,dir:str,id:str) -> List[str]:
        parts = self.file_parts[1:] if self.file_parts[0] == path.sep else self.file_parts
        return path.join(dir, *(part.replace("{id}",id) for part in parts))

    
    """
    build
        build a file descriptors or file sum with the parts of the file paths
        param :
            files : str | List[str]
        return :
            FileDescriptor | FileSum

    """
    @staticmethod
    def build(files:Union[str,List[str]]) -> Union['FileDescriptor',FileSum]:
        if type(files) is str:
            if "{regex}" in files:
                p = PurePath(files.replace("{regex}",""))
                return FileRegex(file_parts=p.parts)
            p = PurePath(files)
            return FileDescriptor(file_parts=p.parts)
        if type(files) is list:
            return FileSum(files=[FileDescriptor.build(file) for file in files])
@dataclass
class HyperParametersConfig:
    dir : str = ''
    output_dir : str = ''
    preprocessing : str = 'default'
    processing : str = 'default'
    realm : str = None
    threshold : Union[float,None] = 3.0
    Atmosphere : dict = field(default_factory=lambda: {'levels':[1000, 850, 700, 500, 200, 100, 10],'unit':'hPa','resolutions':[(None,None)]}) 
    Ocean : dict = field(default_factory=lambda: {'levels':[0, 100, 200, 500, 1000, 2000, 4000],'unit':'m','resolutions':[(None,None)]})
    nan_encoding : int = 255
    chunks_time : float = 0
    chunks_vertical : float = 0
    extension : Extension = Extension.PNG
    lossless : bool = True

    """
        check if the value provided for the key correct
        param :
            key : str
            value : Any 
        return :
            bool
    """
    @staticmethod
    def assert_key_value(key:str,value:Any) -> bool:
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
        if key == "chunks_time" or key == "chunks_vertical":
            return (type(value) is int or type(value) is float) and (value > 0)
        
        if key == "extension" :
            return value in Extension._value2member_map_
        
        if key == "nan_encoding" :
            return type(value) is int
        
        if key == "lossless":
            return type(value) is bool
        if key == "threshold":
            return type(value) is float or type(value) is str
        return True
    """
        change the value of the given to the correct form
        param :
            key : str
            value : Any
        return :
            Any
    """ 
    @staticmethod
    def map_key_value(key,value) ->  Any:
        if key == "Atmosphere" or key == "Ocean":
            if "resolutions" in value:
                value["resolutions"] = [(None if r1 == "default" else r1, None if r2 == "default" else r2) for r1, r2 in value["resolutions"]]
            else :
                value["resolutions"] = [(None,None)]
        if key == "chunks_time" or key == "chunks_vertical":
            if value >= 1:
                value = int(value)

        if key == "extension" :
            value = Extension(value)   
        if key == "lossless" :
            value = bool(value)
        if key == "threshold" :
            if type(value) is str:
                return None
        return value
    """
        bind the create hyper parameters to the previous 
        to set all parameters like the previous one
        param :
            config : HyperParametersConfig
        return :
            HyperParametersConfig
    """
    @staticmethod
    def bind(config:'HyperParametersConfig') -> 'HyperParametersConfig':
        hp = HyperParametersConfig()
        for key,value in config.__dict__.items():
            hp.__dict__[key] = value
        return hp
    """
        set the parameters to the given value if the key exist
        param :
            kargs : dict
        return :
            None
    """
    def extends(self,**kargs) -> None:
        types = self.__annotations__
        for key,value in kargs.items():
            if key in self.__dict__ and HyperParametersConfig.assert_key_value(key,value):
                #if type(value) is types[key]:
                self.__dict__[key] = HyperParametersConfig.map_key_value(key,value)
    """
        build the parameters with the given value if the key exist
        param :
            kargs : dict
        return :
            HyperParametersConfig
    """
    @staticmethod
    def build(**kwargs) -> 'HyperParametersConfig':
        hp = HyperParametersConfig()
        types = hp.__annotations__
        for key,value in kwargs.items():
            if key in hp.__dict__ and HyperParametersConfig.assert_key_value(key,value):
                #if type(value) is types[key]:
                hp.__dict__[key] = HyperParametersConfig.map_key_value(key,value)
        return hp
        
@dataclass
class VariableDescription:
    name : str
    nc_file_var_binder : List[Tuple[Union[FileDescriptor,FileSum,FileRegex],str,bool]]
    hyper_parameters : HyperParametersConfig
    
    """
        build a variable description checking for the inner variables list 
        with correct files and variable names
        param :
            var_desc:dict
            name:str
            hyper_parameters_config:HyperParametersConfig
        return :
            VariableDescription
    """
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
            
            if "optional" in file_var:
                optional = bool(file_var["optional"])
            else :
                optional = False
            
            nc_file_var_binder.append((FileDescriptor.build(files),variable,optional))
        
        return VariableDescription(name=name,\
            nc_file_var_binder=nc_file_var_binder,\
            hyper_parameters=hyper_parameters)
@dataclass
class IdMetadata:
    dir : str
    file : FileDescriptor
    tags : List[str]
    defaults : Dict[str,str]
    labels : List[dict]
    parser : str
    
    def handle(self,id):
        parse = parser.parsers[self.parser]
        def func():
            file = self.file.join(self.dir,id)
            metadata = parse(self.defaults,self.tags,file)
            return metadata
        return func

    @staticmethod
    def build(id_metatada:dict) -> 'IdMetadata':
        dir = id_metatada.get("dir","")
        tags = id_metatada.get("tags",[])
        labels = id_metatada.get("labels",[])
        parser = id_metatada.get("parser","")
        if len(labels) > 0:
            for i in range(len(labels)):
                if type(labels[i]) is str:
                    labels[i] = {
                        "labels" : labels[i],
                        "metadata" : {}
                    }
                elif type(labels[i]) is dict :
                    if "labels" not in labels[i]:
                        raise Exception(f"Malformed labels in config : {labels[i]}\nLabels must be either a string or a dict with \"label\" and \"metadata\"")
                    if "metadata" not in labels[i]:
                        raise Exception(f"Malformed labels in config : {labels[i]}\nLabels must be either a string or a dict with \"label\" and \"metadata\"")
                   
        file = None
        if "file" in id_metatada:
            file = FileDescriptor.build(id_metatada["file"])        
        defaults = {}
        for key,value in id_metatada.items():
            if key not in ("dir","file","tags","labels"):
                defaults[key] = value
        return IdMetadata(
            dir=dir,
            file=file,
            parser=parser,
            tags=tags,
            defaults=defaults,
            labels=labels
        )            

@dataclass
class Config:
    name : str
    supported_variables : Dict[str,VariableDescription]
    hyper_parameters : HyperParametersConfig
    id_metadata : IdMetadata
    """
        get hyper parameters of the variable
        param :
            var_name : str
        return :
            HyperParametersConfig
    """
    def get_hp(self,var_name) -> HyperParametersConfig:
        if var_name in self.supported_variables:
            return self.supported_variables[var_name].hyper_parameters
        return self.hyper_parameters
    
    """
        get realm (either atmosphere or ocean) of the given variable
        and set default resolution if no real;
        param :
            variable : Variable
        return :
            dict
    """
    def get_realm_hp(self,variable) -> dict:
        if variable.realm is None:
            return {"resolutions":[(None,None)]}
            
        if variable.realm.lower() == "a" or variable.realm.lower() == "atmosphere":
            return self.supported_variables[variable.name].hyper_parameters.Atmosphere
        elif variable.realm is not None and (variable.realm.lower() == "o" or variable.realm.lower() == "ocean"):
            return self.supported_variables[variable.name].hyper_parameters.Ocean
        else :
            return {"resolutions":[(None,None)]}
    
    """
        look up the files associatied with the provided variables 
        in the given directory
        and yield the file path, the variable name and the variable
        param :
            input_folder:str
            id:str
            variables:list
        return :
            Generator of ( (str | List[str]) , str, Any)
    """
    def look_up(self,input_folder:str,id:str,variable) -> Generator[Tuple[Union[str,List[str]],str,Any], None, None]:
        
        dir = input_folder if input_folder != self.get_hp(variable.name).dir else self.get_hp(variable.name).dir 

        if variable.name in self.supported_variables:
            supported_variable = self.supported_variables[variable.name]
            for file_desc,var_name,optional in supported_variable.nc_file_var_binder:
                if type(file_desc) is FileDescriptor:
                    file_path = file_desc.join(dir,id)
                    if path.isfile(file_path):
                        yield file_path,var_name
                    elif not optional :
                        raise FileNotFoundError
                elif type(file_desc) is FileSum:
                    file_paths = file_desc.join(dir,id)
                    if len(file_paths) != 0 and all(path.isfile(file_path) for file_path in file_paths):
                        yield file_paths,var_name
                    elif not optional :
                        raise FileNotFoundError
                elif type(file_desc) is FileRegex:
                    file_paths = file_desc.join(dir,id)
                    if len(file_paths) != 0 and all(path.isfile(file_path) for file_path in file_paths):
                        yield file_paths,var_name
                    elif not optional :
                        raise FileNotFoundError
    """
        build the config with the path to the toml files
        param :
            desc : str
        return :
            Config
    """
    
    @staticmethod
    def _build(config:dict,desc:str) -> 'Config':
        if "Model" not in config :
            raise ConfigException(f"{desc} is not a valid config file, please provide a Model tag")
        model = config["Model"]
        if "dir" not in model:
            raise ConfigException(f"{desc} is not a valid config file, please provide a directory in the Model tag")
        #directory = model["dir"]
        if "name" not in model:
            raise ConfigException(f"{desc} is not a valid config file, please provide a name in the Model tag")
        name = model["name"]
        
        if "metadata" in model:
            id_metadata = IdMetadata.build(model["metadata"])
        else :
            id_metadata = None

        hyper_parameters = HyperParametersConfig.build(**model)
        
        supported_variable = {}
        
        for var_name,var_desc in config.items():
            if var_name == "Model":
                continue
            supported_variable[var_name] = VariableDescription.build(var_desc=var_desc,name = var_name,hyper_parameters_config = hyper_parameters)
            
        return Config(
            name=name,
            supported_variables=supported_variable,
            hyper_parameters=hyper_parameters,
            id_metadata=id_metadata
        )


    
    
    @staticmethod
    def build(desc:str) -> 'Config':
        if not path.isfile(desc) and path.basename(desc).split('.')[-1] == "toml":
            raise ConfigException(f"{desc} is not a valid toml file")
        with open(desc,mode="rb") as fp:
            config = tomli.load(fp)
        return Config._build(config=config,desc=desc)


    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)