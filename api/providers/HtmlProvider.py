import codecs
from dataclasses import dataclass
from logging import Logger
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
        data.update(HtmlProvider.retrieve_publication_info(soup, tags))
        exps = soup.find('table', {"id" : "Simulations"} )        
        data["expts_web"] = []
        rows = exps.find_all('tr')
        if len(rows) > 1 :
            if len(rows[1].find_all('td')) == 3 :
                data["expts_web"].extend(self.find_experiments(rows))
            elif len(rows[1].find_all('td')) == 2 :
                data["expts_web"].extend(HtmlProvider.experiments_when_2_columns(rows = rows))
        #check types
        if "year" in data:
            year = to_int(data["year"])
            if year is not None:
                data["year"] = to_int(data["year"])
            else :
                del data["year"]
        return data
    
    @staticmethod
    def experiments_when_2_columns(rows):
        exps = []
        label = rows[0].find('th').text.strip()
        for exp in rows:
            td = exp.find_all('td')
            a = exp.find('a')
            if a:
                exps.append({"exp_id" : a.text.strip(), 
                             "labels" : [{"label" : label, "metadata" : {"text" : td[0].text.strip()} }] })
        return exps

    
    def find_experiments(self, rows):
            all_exps = []
            label_1 = rows[0].find('th').text.strip()
            label_2 = rows[0].find_all('th')[1].text.strip()
            for sequence in rows:
                a = sequence.find_all('a')
                if a :
                    metadata_1 = {"text" : sequence.find('td').text.strip()}
                    metadata_2 = {"text" : a[0].text.strip()}
                    url = a[1].attrs['href']
                    exps = []
                    html_text = HtmlProvider.retrieve_html_text(self.url, url, self.files)
                    soup = BeautifulSoup(html_text, 'html.parser') 
                    first_row = soup.find(text = "Experiment Name").parent.parent.parent
                    label_age = first_row.find_all('strong')[-1].text.strip()
                    for tr in first_row.find_next_siblings():
                        a = tr.find("a")
                        age = tr.find_all('td')[-1]
                        if a :
                            exps.append({"exp_id" : a.text.strip(), 
                                "labels" : [{"label" : label_1, "metadata" : metadata_1}, 
                                            {"label" : label_2, "metadata" : metadata_2}, 
                                            {"label" : label_age, "metadata" : {"age" : age.text.strip()}}
                            ]})
                    all_exps.extend(exps)
            return all_exps    

    @staticmethod
    def retrieve_html_text(url_base, url, files):
        html_text = ""
        if url_base != None and len(files) == 0:
            try :
                url_parse = urlparse(url_base)._replace(path = url)
                req = requests.get(url_parse.geturl())
                if req.ok :
                    html_text = req.text
            except :
                pass
        else :
            #create the path from the url and the filepaths in self.files
            if path.exists(url):
                html_text = codecs.open(url, "r",  encoding='utf-8', errors='ignore').read()
            else :
                Logger.console().warning(f"local path {url} not found")
        return html_text        

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