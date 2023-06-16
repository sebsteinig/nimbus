from dataclasses import dataclass
import os.path as path
from os import listdir
from utils.metadata import parser


TAGS = ["title", "authors_short", "authors_full", "journal", "year", "volume", "pages",\
             "doi", "owner_name", "owner_email", "abstract", "brief_desc", "expts_web"]

def to_int(_data):
    try:
        return int(_data)
    except :
        None
def to_list(_data):
    if _data.startswith('(') and _data.endswith(')'):
        return _data[1:-1].split() 
    elif _data.startswith('"(') and _data.endswith(')"'):
        return _data[2:-2].split('" "')
    elif _data.startswith('("') and _data.endswith('")'):
        return _data[2:-2].split('" "') 
    return None

@dataclass
class DatProvider:
    files : list 
    
    def parse(self,default_tags,tags) -> dict :
        res = {}
        for file in self.files:
            data = parser.dat_parse(default_tags, tags, file)
            if "year" in data:
                data["year"] = to_int(data["year"])
            if "expts_web" in data:
                data["expts_web"] = list(set(to_list(data["expts_web"])))
            res[path.basename(file).split(".")[0]] = data
        return res
    
    @staticmethod
    def build(filepath : str) -> 'DatProvider':
        blacklist = ("default_settings.dat")
        if path.isfile(filepath) and filepath.endswith("dat"):
            return DatProvider(files=[filepath])
        return DatProvider(
            files = [path.join(filepath, file) for file in listdir(filepath) if file not in blacklist and file.endswith("dat")]
        )
