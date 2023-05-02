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

def import_submodules(package_name):
    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + '.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
    }

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
                and sv.hyper_parameters.preprocessing in obj["preprocessing"]:
                preprocess = obj["preprocessing"][sv.hyper_parameters.preprocessing]
            
            process = utils.default_processing
            
            if sv.hyper_parameters.processing != "default"\
                and sv.hyper_parameters.processing in obj["processing"]:
                process = obj["processing"][sv.hyper_parameters.processing]
                 
            
            variable = Variable(
                name=key,\
                realm = obj["realm"] if sv.hyper_parameters.realm is None else sv.hyper_parameters.realm,\
                preprocess=preprocess,\
                process=process,\
            )
            variables.append(variable)
            
    return variables

