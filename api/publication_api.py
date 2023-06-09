from dataclasses import dataclass
import json
import os.path as path
from api.providers.DatProvider import DatProvider
from dotenv import dotenv_values
import requests
from api.providers.HtmlProvider import HtmlProvider

from utils.logger import Logger

@dataclass
class PublicationAPI:
    dat_provider : DatProvider
    html_provider : HtmlProvider
    url : str
    api_key : str
    
    def send(self) :
        data = self.merge()
        try :    
            res = requests.post(
                self.url,
                json=data,
                cookies={"access_token":self.api_key}
            )    
            
            if res.status_code == 409:
                response = json.load(res.text)
                if "requested_id" in response:
                    self.notify(response["requested_id"])
            elif not res.ok :
                Logger.console().error(f"Status code : {res.status_code} for :\n{res.text}")
        except Exception as e:
            Logger.console().error(e)
        
        
    def merge(self) -> dict:
        default_tags= {}
        tags = []
        
        dat_data = self.dat_provider.parse(default_tags,tags)
        #clean dat data
        for file in dat_data:
            for key,value in dat_data[file].items():
                if value is None or value == "":
                    del dat_data[file][key]
        print("DAT :")
        print(dat_data)
        
        html_data = self.html_provider.parse(default_tags,tags)
        #clean html data
        for file in html_data:
            for key,value in html_data[file].items():
                if value is None or value == "":
                    del html_data[file][key]
        
        print("HTML :") 
        print(html_data)
        
        # merge 
        merged_data = dat_data
        merged_data.update(html_data)
        merged_data = list(merged_data.values())
        
        #grep all exp ids
        _exp_ids = [publication["expts_web"] for publication in merged_data]
        exp_ids = []
        for ids in _exp_ids:
            exp_ids.extend(ids)
        exp_ids = list(set(exp_ids))
        
        
        data = {
            "publication" : merged_data,
            "exp_ids" : exp_ids,
        }

        return data
        
    def notify(requested_exp_ids:list) :
        Logger.console().warning(requested_exp_ids)
        
    
    @staticmethod
    def build(filepath : str) -> 'PublicationAPI':
        if not path.exists(filepath):
            raise Exception(f"{filepath} does not exist")
        
        route = "insert/publication"
        config = dotenv_values(".env")
        url = f"{config['ARCHIVE_DB_URL']}/{route}"
        api_key = config['API_KEY']
        
        dat_provider = DatProvider.build(filepath)
        html_provider = HtmlProvider.build(filepath)
        return PublicationAPI(
            dat_provider = dat_provider,
            html_provider = html_provider,
            url = url,
            api_key = api_key,
        )