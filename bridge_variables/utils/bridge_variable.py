
from typing import List,Union,Callable,Any

def bridge_preprocessing(*args):
    assert(len(args) == 1)
    cls = args[0]
    def inner(func):
        def preprocess_function():
            return func
        cls.preprocess_function = preprocess_function
        return func
    return inner

def bridge_processing(*args):
    assert(len(args) == 1)
    cls = args[0]
    def inner(func):
        def process_function():
            return func
        cls.process_function = process_function
        return func
    return inner


def bridge_variable(cls):
    attribut_names_lower = [name.lower() for name in cls.__dict__.keys()]
    #attribut_names = list(cls.__dict__.keys())
    if not (("realm" in attribut_names_lower 
            and "output_stream" in attribut_names_lower)\
        or ("inidata" in attribut_names_lower)):
        raise Exception(f"Realm and Output stream or inidata are missing")
    
    class BridgeVariable(cls):
        preprocess_function:Any
        process_function:Any
        realm = cls.realm if "realm" in cls.__dict__ else None
        output_stream = cls.output_stream if "output_stream" in cls.__dict__ else None
        look_for = cls.look_for if "look_for" in cls.__dict__ else None
        inidata = cls.inidata if "inidata" in cls.__dict__ else None
        
        def __init__(self, *args, **kargs):
            super(BridgeVariable, self).__init__(*args, **kargs)
        
        def build(self) -> dict:
            look_for = BridgeVariable.look_for
            if type(look_for) is str:
                look_for = (look_for,)
            
            return {
                'realm' : BridgeVariable.realm,
                'output_stream' : BridgeVariable.output_stream,
                'inidata' : BridgeVariable.inidata,
                'look_for':look_for,
                'preprocessing' : BridgeVariable.preprocess_function(),
                'processing' : BridgeVariable.process_function(),
            }
                
    
    return BridgeVariable