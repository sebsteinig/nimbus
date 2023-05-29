from datetime import datetime, timedelta
import json
from utils.logger import Logger
from utils.metadata import Metadata
from dataclasses import dataclass
from typing import List, Union
import requests
from dotenv import dotenv_values
import os.path as path
from os import listdir, mkdir, remove

@dataclass
class ArchiveDB:
    url:str
    experiments : dict
    commit_dir : str
    api_key : str
    
    def add(self,exp_id:str,
            variable_name:str,
            files_ts:List[str],
            files_mean:List[str],
            config_name:str,
            rx:Union[float,None],
            ry:Union[float,None],
            extension:str,
            lossless:bool,
            chunks:float,
            metadata:Metadata):
        table_nimbus_execution_row = {
            "exp_id":exp_id,
            "config_name":config_name,
            "created_at":(datetime.now() - timedelta(days=10)).isoformat(),
            "extension":extension,
            "lossless":lossless,
            "nan_value_encoding":metadata.general_metadata.nan_value_encoding,
            "threshold":metadata.general_metadata.threshold,
            "chunks":chunks,
            "rx":0 if rx is None else rx,
            "ry":0 if ry is None else ry,
        }
        table_variable_row = {
            "name":variable_name,
            "paths_ts":files_ts,
            "paths_mean":files_mean,
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
            self.experiments[exp_id] = {
                'table_nimbus_execution' : table_nimbus_execution_row,
                'table_variable' : [table_variable_row]
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