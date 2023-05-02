
from typing import Dict, List,Union,Callable,Any

def preprocessing(*args):
    assert(len(args) >= 1)
    cls = args[0]
    model = "default" if len(args) < 2 else args[1].lower()
    def inner(func):
        cls.preprocess_functions[model] = func
        return func
    return inner

def processing(*args):
    assert(len(args) >= 1)
    cls = args[0]
    model = "default" if len(args) < 2 else args[1].lower()
    def inner(func):
        cls.process_functions[model] = func
        return func
    return inner


def supported_variable(cls):
    attribut_names_lower = [name.lower() for name in cls.__dict__.keys()]
    #attribut_names = list(cls.__dict__.keys())
    
    class SupportedVariable(cls):
        preprocess_functions:Dict[str,Any]={}
        process_functions:Dict[str,Any]={}
        realm = cls.realm if "realm" in cls.__dict__ else None
        
        def __init__(self, *args, **kargs):
            super(SupportedVariable, self).__init__(*args, **kargs)
        
        def build(self) -> dict:
            
            return {
                'realm' : SupportedVariable.realm,
                'preprocessing' : SupportedVariable.preprocess_functions,
                'processing' : SupportedVariable.process_functions,
            }
                
    
    return SupportedVariable