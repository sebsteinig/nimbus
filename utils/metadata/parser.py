
import json

from dotenv import dotenv_values

parsers = {}

def For(*names):
    def wrapper(func):
        for name in names:
            parsers[name.lower()] = func
        return func
    return wrapper

@For("bridge","dat")
def bridge_parse(default_tags:dict,tags,file):
    
    config = dotenv_values(file)
    metadata = default_tags.copy()
    for tag in tags:
        if tag in config:
            metadata[tag] = config[tag]
    return metadata

def retrieve_value(value : str):
    if value.startswith("(") and value.endswith(")"):
        if value.find('"') != -1:
            res = value.removeprefix("(").removesuffix(")")
            res = res.split('" "')
            res[0] = res[0].removeprefix('"')
            res[-1] = res[-1].removesuffix('"')
        else :
            res = value.removeprefix("(").removesuffix(")").split(" ")
        return res
    else:
        return value.replace('"','')
    

@For("json")
def json_parse(default_tags:dict,tags,file):
    metadata = default_tags.copy()
    with open(file,'r') as f:
        _json = json.loads(f.read())
        if tags is None or len(tags) == 0:
            metadata.update(_json)
        for key,value in _json.items():
            if key in tags:
                metadata.update(json.loads(f.read()))
    return metadata

@For("")
def default_parse(default_tags:dict,tags,file):
    metadata = default_tags.copy()
    extension = file.split(".")[-1]
    if extension in parsers:
        return parsers[extension](default_tags,tags,file)
    else :
        raise Exception(f"{extension} extension not supported")
    