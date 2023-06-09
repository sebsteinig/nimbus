from dataclasses import dataclass
import json
import os.path as path
from api.providers.DatProvider import DatProvider
from dotenv import dotenv_values
import requests

from utils.logger import Logger

@dataclass
class PublicationAPI:
    dat_provider : DatProvider
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
        except Exception as e:
            Logger.console().error(e)
        
        
    def merge(self) -> dict:
        default_tags= {}
        tags = []
        
        dat_data = self.dat_provider.parse(default_tags,tags)
    

        return dat_data
        
    def notify() :
        pass
    
    @staticmethod
    def build(filepath : str) -> 'PublicationAPI':
        if not path.exists(filepath):
            raise Exception(f"{filepath} does not exist")
        
        route = "insert/publication"
        config = dotenv_values(".env")
        url = f"{config['ARCHIVE_DB_URL']}/{route}"
        api_key = config['API_KEY']
        
        dat_provider = DatProvider.build(filepath)
        return PublicationAPI(
            dat_provider = dat_provider,
            url = url,
            api_key = api_key,
        )