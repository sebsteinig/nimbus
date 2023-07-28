from datetime import datetime, timedelta
import json

import numpy as np
from utils.logger import Logger
from utils.metadata.metadata import Metadata
from dataclasses import dataclass
from typing import List, Union
import requests
from dotenv import dotenv_values
import os.path as path
from os import listdir, mkdir, remove

def to_grid(list_files,chunks_t,chunks_v):
    grids = []
    for files in list_files:
        grid = [[None for t in range(chunks_t)] for v in range(chunks_v)]
        for file in files :
            desc = path.basename(file).split(".")
            t = 1
            v = 1
            for d in desc[2:]:
                if "of" in d :
                    if d[0] == 't':
                        t = int(d[1:].split("of")[0])
                    if d[0] == 'v':
                        v = int(d[1:].split("of")[0])
            grid[v-1][t-1] = file
        
        grid = [[cell for cell in row if cell is not None] for row in grid]
        grid = [ row for row in grid if len(row) > 0]
        grids.append({"grid":grid})
    return grids

@dataclass
class ArchiveDB:
    url:str
    experiments : dict
    commit_dir : str
    api_key : str
    
    def add(self,exp_id:str,
            variable_name:str,
            list_files_ts:List[List[str]],
            list_files_mean:List[List[str]],
            config_name:str,
            rx:Union[float,None],
            ry:Union[float,None],
            extension:str,
            lossless:bool,
            id_metadata:dict,
            chunks_t:int,
            chunks_v:int,
            metadata:Metadata):
        
        ct = chunks_t if chunks_t > 1 else 1
        cv = chunks_v if chunks_v > 1 else 1
        paths_ts = to_grid(list_files_ts,ct,cv)
        paths_mean = to_grid(list_files_ts,ct,cv)
        
        
        table_nimbus_execution_row = {
            "exp_id":exp_id,
            "config_name":config_name,
            "created_at":(datetime.now() - timedelta(days=10)).isoformat(),
            "extension":extension,
            "lossless":lossless,
            "nan_value_encoding":metadata.general_metadata.nan_value_encoding,
            "threshold":metadata.general_metadata.threshold,
            "rx":0 if rx is None else rx,
            "ry":0 if ry is None else ry,
        }

        table_variable_row = {
            "name":variable_name,
            "paths_ts":{"paths":paths_ts},
            "paths_mean":{"paths":paths_mean},
            "levels":metadata.general_metadata.levels,
            "timesteps":metadata.general_metadata.timesteps,
            "xsize":metadata.general_metadata.xsize,
            "xfirst":metadata.general_metadata.xfirst,
            "xinc":metadata.general_metadata.xfirst,
            "ysize":metadata.general_metadata.ysize,
            "yfirst":metadata.general_metadata.yfirst,
            "yinc":metadata.general_metadata.yinc,
            "metadata":{"metadata":[vs.to_dict() for vs in metadata.vs_metadata]},
        }
        if exp_id in self.experiments:
            self.experiments[exp_id]['table_variable'].append(table_variable_row)
        else :
            if "date_original" in id_metadata["metadata"]:
                id_metadata["metadata"]["date_original"] = datetime.strptime(id_metadata["metadata"]["date_original"], '%Y_%m_%d_%H_%M').isoformat()
            if "date_modified" in id_metadata["metadata"]:
                id_metadata["metadata"]["date_modified"] = datetime.strptime(id_metadata["metadata"]["date_modified"], '%Y_%m_%d_%H_%M').isoformat()

            if "realistic" in (l.lower() for l in id_metadata["labels"]):
                id_metadata["metadata"]["realistic"] = True
                for i in [i for i,l in enumerate(id_metadata["labels"]) if l.lower() == "realistic"]:
                    del id_metadata["labels"][i]

            for i in range(len(id_metadata["labels"])):
                if type(id_metadata["labels"][i]) is str:
                    id_metadata["labels"][i] = {
                        "labels" : id_metadata["labels"][i],
                        "metadata" : {}
                    }

            self.experiments[exp_id] = {
                'table_nimbus_execution' : table_nimbus_execution_row,
                'table_variable' : [table_variable_row],
                'exp_metadata' : id_metadata
            }
    
    def commit(self):
        if not path.isdir(self.commit_dir) :
            mkdir(self.commit_dir)
        for exp_id,rows in self.experiments.items():
            commit_file = path.join(self.commit_dir,f"commit_{exp_id}_{datetime.now().strftime('%d_%m_%Y_%H:%M')}.json")
            with open(commit_file,"w") as file:
                file.write(json.dumps({
                    "date": datetime.now().isoformat(),
                    "exp_id":exp_id,
                    "body" : {"request":rows}
                }))
        
    def push(self) -> bool:
        if not path.isdir(self.commit_dir) :
            result = True
            for exp_id,rows in self.experiments.items():
                url = f"{self.url}/insert/{exp_id}"
                try :
                    res = requests.post(url,json={"request":rows},cookies={"access_token":self.api_key})          
                    if not res.ok:
                        result = False
                except :
                    result = False
            return result
        else :
            result = True
            requests_list = []
            for file in listdir(self.commit_dir):
                with open(path.join(self.commit_dir,file),'r') as rd :
                    requests_list.append((path.join(self.commit_dir,file),json.loads(rd.read())))
            requests_list.sort(key=lambda item:datetime.fromisoformat(item[1]['date']), reverse=True)
            for file,request in requests_list:
                url = f"{self.url}/insert/{request['exp_id']}"
                try :
                    res = requests.post(url,json=request['body'],cookies={"access_token":self.api_key})
                    if res.ok:
                        remove(file)
                    else :
                        result = False
                except :
                    result = False
            return result
    @staticmethod
    def build() -> 'ArchiveDB':
        config = dotenv_values(".env")
        
        return ArchiveDB(
            api_key =  config["API_KEY"],
            commit_dir = "./migrations",
            url = config["ARCHIVE_DB_URL"],
            experiments={}
        )