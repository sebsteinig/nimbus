
from typing import Dict, List,Union,Callable,Any

"""
    annototion used for adding the preprocessing function
    to the given class for the given model
    param :
        cls : type (A Class)
        model : str (Will be set to lowercase)
    return :
        annotation
"""
def preprocessing(cls:type,model:str = "default"):
    model = model.lower()
    def inner(func):
        cls.preprocess_functions[model] = func
        return func
    return inner

"""
    annototion used for adding the processing function
    to the given class for the given model
    param :
        cls : type (A Class)
        model : str (Will be set to lowercase)
    return :
        annotation
"""
def processing(cls:type,model:str = "default"):
    model = model.lower()
    def inner(func):
        cls.process_functions[model] = func
        return func
    return inner

"""
    class annototation to transform the given class 
    to a supported variable class with a realm, preprocessing functions (by model),
    and processing functions (by model)
    param :
        cls : type (A Class)
    return :
        annotation
"""
def supported_variable(cls):
    attribut_names_lower = [name.lower() for name in cls.__dict__.keys()]
    
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