
import json


parsers = {}

def For(*names):
    def wrapper(func):
        for name in names:
            parsers[name.lower()] = func
        return func
    return wrapper

@For("bridge","dat")
def bridge_parse(default_tags:dict,tags,file):
    metadata = default_tags.copy()
    with open(file,'r') as f:
        for line in f.readlines():
            _splitted = line.strip().split('=')
            key,value = _splitted[0],_splitted[-1].replace('"','')
            if key in tags:
                metadata[key] = value
    return metadata

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
    