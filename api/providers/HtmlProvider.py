import codecs
from dataclasses import dataclass
import requests
import os.path as path
from urllib.parse import urlparse
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
    html_text : str
    url : str

    
    def parse(self,default_tags:dict,tags:list) -> dict :
        tags = {key:tag for key,tag in TAGS.items() if tag in tags}
        res = {}
        if len(self.files) == 0 and self.html_text != None:
            data = self.parse_html(self.html_text, tags, default_tags.copy())
            res[self.url.split("/")[-1].split(".")[0]] = data
        else:    
            for file in self.files:
                with codecs.open(file, "r",  encoding='utf-8', errors='ignore') as f:
                    data = self.parse_html(f.read(), tags, default_tags.copy())
                    res[path.basename(file).split(".")[0]] = data  
        print(res)
        return res
    

    @staticmethod   
    def retrieve_publication_info(soup, tags : dict) -> dict:
        info = {}
        rows = soup.find_all('tr')
        for row in rows:
            th = row.find('th')
            if th :
                if th.text.strip() in tags.keys():
                    td = row.find('td')
                    if td:
                        info[tags[th.text.strip()]] = td.text.strip()
        return info
    
    def parse_html(self, html_string : str, tags : dict, data : dict):
        soup = BeautifulSoup(html_string, 'html.parser')    
        res = {"expts_web" : [], "expts_paper" : []}
        res.update(HtmlProvider.retrieve_publication_info(soup, tags))
        exps = soup.find('table', {"id" : "Simulations"} )
        for exp in exps.find_all('tr'):
            td = exp.find_all('td')
            a = exp.find_all('a')
            #if 3 columns : we get the data from the next webpage
            if len(td) == 3 :
                res["expts_web"].extend(self.find_experiments(a[1].attrs['href']))
            elif len(td) == 2:
                res["expts_paper"].append(td[0].text.strip())
                if a:
                    res["expts_web"].append(a[0].text.strip())
        data.update(res)
        #check types
        if "year" in data:
            year = to_int(data["year"])
            if year is not None:
                data["year"] = to_int(data["year"])
            else :
                del data["year"]                        
        return data
    
    
    def find_experiments(self, url : str):
            res = []
            if self.url != None and len(self.files) == 0:
                try :
                    url_parse = urlparse(self.url)._replace(path = url)
                    req = requests.get(url_parse.geturl())
                    if not req.ok :
                        return res
                    html_text = req.text
                except :
                    return res
            else :
                if path.exists(url):
                    html_text = codecs.open(url, "r",  encoding='utf-8', errors='ignore').read()
            soup = BeautifulSoup(html_text, 'html.parser') 
            first_row = soup.find(text = "Experiment Name").parent.parent.parent
            for tr in first_row.find_next_siblings():
                a = tr.find("td").find("a")
                if a :
                    res.append(a.text.strip())
            return res

    #with local folder or file
    @staticmethod
    def build(filepath : str) -> 'HtmlProvider':
        blacklist = ("default_settings.dat")
        if path.isfile(filepath):            
            return HtmlProvider(files=[filepath.replace("dat","html")], html_text = None, url = None)
        return HtmlProvider(
            files = [path.join(filepath, file.replace("dat","html")) for file in listdir(filepath) if file not in blacklist and file.endswith("dat")],
            html_text = None,
            url = None
        )    

    #with url
    @staticmethod
    def build_from_src(url : str) -> 'HtmlProvider':
        blacklist = ("default_settings.dat")
        r = requests.get(url)
        return HtmlProvider(files = [], html_text = r.text, url = url), r.ok