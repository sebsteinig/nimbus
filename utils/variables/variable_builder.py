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
            variable = Variable(
                name=key,\
                realm = obj["realm"],\
                preprocess=\
                    utils.default_preprocessing \
                        if config.name.lower() not in obj["preprocessing"] \
                    else obj["preprocessing"][config.name.lower()],\
                process=\
                    utils.default_processing \
                        if config.name.lower() not in obj["processing"] \
                    else obj["processing"][config.name.lower()],\
            )
            variables.append(variable)
            
    return variables

