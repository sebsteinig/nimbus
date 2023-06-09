from dataclasses import dataclass
import os.path as path
from os import listdir
from bs4 import BeautifulSoup

TAGS = {"Name" : "authors_short", "Title" : "title", 
        "Full Author List" : "authors_full", "Journal":"journal",
        "Year":"year", "Volume":"volume", "Pages":"pages", "DOI":"doi", 
        "Contact's Name":"owner_name", "Contact's email":"owner_email",
        "Abstract" : "abstract", "Brief Description" : "brief_desc"}

def to_int(_data):
    try:
        return int(_data)
    except :
        None

@dataclass
class HtmlProvider:
    files : list 
    
    def parse(self,default_tags:dict,tags:list) -> dict :
        tags = {key:tag for key,tag in TAGS.items() if tag in tags}
        res = {}
        for file in self.files:
            with open(file, "r") as f:
                data = default_tags.copy()
                data.update(HtmlProvider.parse_html(f.read(), tags))
            if "year" in data:
                year = to_int(data["year"])
                if year is not None:
                    data["year"] = to_int(data["year"])
                else :
                    del data["year"]
            res[path.basename(file).split(".")[0]] = data
        return res
    @staticmethod   
    def parse_html(html_string : str, tags : dict):
        soup = BeautifulSoup(html_string, 'html.parser')    
        res = {"expts_web" : [], "expts_paper" : []}
        rows = soup.find_all('tr')
        for row in rows:
            th = row.find('th')
            if th :
                if th.text.strip() in tags.keys():
                    td = row.find('td')
                    if td:
                        res[tags[th.text.strip()]] = td.text.strip()
        exps = soup.find('table', {"id" : "Simulations"} )
        for exp in exps.find_all('tr'):
            td = exp.find('td')
            if td :
                res["expts_paper"].append(td.text.strip())
            a = exp.find('a')
            if a:
                res["expts_web"].append(exp.text.strip())
        return res
    
    
    @staticmethod
    def build(filepath : str) -> 'HtmlProvider':
        blacklist = ("default_settings.dat")
        if path.isfile(filepath):
            
            return HtmlProvider(files=[filepath.replace("dat","html")])
        return HtmlProvider(
            files = [path.join(filepath, file.replace("dat","html")) for file in listdir(filepath) if file not in blacklist and file.endswith("dat")]
        )
