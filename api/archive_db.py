from utils.logger import Logger
from utils.metadata import Metadata
from dataclasses import dataclass
from typing import List, Union
import requests
from dotenv import dotenv_values

@dataclass
class ArchiveDB:
    url:str
    experiments : dict
    
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
        row = {
            "name":variable_name,
            "exp_id":exp_id,
            "paths_ts":files_ts,
            "paths_mean":files_mean,
            "config_name":config_name,
            "levels":metadata.general_metadata.levels,
            "timesteps":metadata.general_metadata.timesteps,
            "xsize":metadata.general_metadata.xsize,
            "xfirst":metadata.general_metadata.xfirst,
            "xinc":metadata.general_metadata.xfirst,
            "ysize":metadata.general_metadata.ysize,
            "yfirst":metadata.general_metadata.yfirst,
            "yinc":metadata.general_metadata.yinc,
            "extension":extension,
            "lossless":lossless,
            "nan_value_encoding":metadata.general_metadata.nan_value_encoding,
            "threshold":metadata.general_metadata.threshold,
            "chunks":chunks,
            "rx":0 if rx is None else rx,
            "ry":0 if ry is None else ry,
            "metadata":{"metadata":[vs.to_dict() for vs in metadata.vs_metadata]},
        }
        if exp_id in self.experiments:
            self.experiments[exp_id].append(row)
        else :
            self.experiments[exp_id] = [row]
    
    def commit(self):
        #print(self.experiments)
        
        pass
        
    def push(self) -> bool:
        for exp_id,rows in self.experiments.items():
            url = f"{self.url}/experiment/{exp_id}/add"
            Logger.console().info(url)
            Logger.console().info([row["name"] for row in rows])
            res = requests.post(url,json={"variables":rows})
            Logger.console().info(res.status_code)
            Logger.console().info(res.text)
            
    @staticmethod
    def build() -> 'ArchiveDB':
        config = dotenv_values(".env")
        
        return ArchiveDB(
            url = config["ARCHIVE_DB_URL"],
            experiments={}
        )