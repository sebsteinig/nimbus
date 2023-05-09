if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)

import importlib
import pkgutil
from typing import Dict
from utils.config import Config
from utils.variables.variable import *
from cdo import Cdo
import supported_variables
import supported_variables.utils.utils as utils
import sys, inspect

"""
    import the submodules of the given module
    param :
        package_name : module
    return :
        Dict[str,module]
"""
def import_submodules(package_name):
    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + '.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
    }
"""
    build the supported variables by scanning and importing 
    the modules from the supported_variables folder and retrieving 
    for each modules the SupportedVariable class with the correct information
    set the variables with their corresponding attribut or with their default attribut 
    according to the config
    param :
        config : Config
    return :
        List[Variables]
"""
def build(config:Config):
    sub_modules = import_submodules(supported_variables.__name__)
    variables = []
    for key,value in sub_modules.items():
        clsmembers = inspect.getmembers(value, inspect.isclass)
        
        cls = [cls for cls in clsmembers if cls[1].__name__ == "SupportedVariable"]
        assert(len(cls) == 1)
        cls = cls[0][1]
        obj = cls().build()
        
        if key in config.supported_variables:
            sv = config.supported_variables[key]
            preprocess = utils.default_preprocessing
            
            if sv.hyper_parameters.preprocessing != "default"\
                and sv.hyper_parameters.preprocessing.lower() in obj["preprocessing"]:
                preprocess = obj["preprocessing"][sv.hyper_parameters.preprocessing.lower()]
            
            process = utils.default_processing
            
            if sv.hyper_parameters.processing != "default"\
                and sv.hyper_parameters.processing.lower() in obj["processing"]:
                process = obj["processing"][sv.hyper_parameters.processing.lower()]
                 
            
            variable = Variable(
                name=key,\
                realm = obj["realm"] if sv.hyper_parameters.realm is None else sv.hyper_parameters.realm,\
                preprocess=preprocess,\
                process=process,\
            )
            variables.append(variable)
            
    return variables

