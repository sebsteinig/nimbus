import importlib
import pkgutil
from typing import Dict
from utils.variables.variable import *
from cdo import Cdo
import bridge_variables
import sys, inspect

def import_submodules(package_name):
    """ Import all submodules of a module, recursively

    :param package_name: Package name
    :type package_name: str
    :rtype: dict[types.ModuleType]
    """
    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + '.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
    }

def build():
    sub_modules = import_submodules(bridge_variables.__name__)
    requests = {}
    for key,value in sub_modules.items():
        clsmembers = inspect.getmembers(value, inspect.isclass)
        
        cls = [cls for cls in clsmembers if cls[1].__name__ == "BridgeVariable"]
        assert(len(cls) == 1)
        cls = cls[0][1]
        obj = cls().build()
        
        requests[key] = {
            "variable":Variable(name=key,look_for=obj["look_for"],preprocess=obj["preprocessing"],process=obj["processing"]),\
            "output_stream":obj["output_stream"],\
            "realm":obj["realm"],
            "inidata":obj["inidata"]
        }
    return requests

if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)