import codecs
from dataclasses import dataclass
from logging import Logger
import requests
import os.path as path
from urllib.parse import urlparse
from os import listdir
from utils.logger import Logger
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
    folder : str
    
    """
    parse for each file in files or directly the html_text if a url was given
        param :
            default_tags:dict
            tags:list
        return :
            dict
    """
    def parse(self,default_tags:dict,tags:list) -> dict :
        tags = {key:tag for key,tag in TAGS.items() if tag in tags}
        res = {}
        if self.html_text != None:
            data = self.parse_html(self.html_text, tags, default_tags.copy())
            if len(data.keys()) == 0:
                Logger.console().warning(f"data from {file} will be ignored")
            else :
                res[self.url.split("/")[-1].split(".")[0]] = data
        else:    
            for file in self.files:
                with codecs.open(file, "r",  encoding='utf-8', errors='ignore') as f:
                    data = self.parse_html(f.read(), tags, default_tags.copy())
                    if len(data.keys()) == 0:
                        Logger.console().warning(f"data from {file} will be ignored")
                    else :
                        res[path.basename(file).split(".")[0]] = data 
        return res
    
    """
    parse the html source text
        param :
            html_string : str
            tags : dict
            data : dict
        return :
            dict
    """
    def parse_html(self, html_string : str, tags : dict, data : dict) -> dict:
        soup = BeautifulSoup(html_string, 'html.parser')    
        data.update(HtmlProvider.retrieve_publication_info(soup, tags))
        exps = soup.find('table', {"id" : "Simulations"} )        
        data["expts_web"] = []
        rows = exps.find_all('tr')
        if len(rows) > 1 :
            number_columns = len(rows[1].find_all('td'))
            if  number_columns == 3 :
                exps = self.find_experiments(rows)
                if len(exps) == 0 :
                    return {}
                data["expts_web"].extend(exps)
            elif number_columns == 2 :
                data["expts_web"].extend(HtmlProvider.experiments_when_2_columns(rows))
        #check types
        if "year" in data:
            year = to_int(data["year"])
            if year is not None:
                data["year"] = to_int(data["year"])
            else :
                del data["year"]
        return data

    """
    every information except the exp_id are parsed with this function
        param :
            soup : BeautifulSoup
            tags : dict
        return :
            dict
    """
    @staticmethod   
    def retrieve_publication_info(soup : BeautifulSoup, tags : dict) -> dict:
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
    
    """
    experiment parsing when there are 2 columns in the html table
        param :
            rows : contains every row of the table
        return :
            list of the experiment ids with their labels
    """
    @staticmethod
    def experiments_when_2_columns(rows) -> list:
        exps = []
        label = rows[0].find('th').text.strip()
        for exp in rows:
            td = exp.find_all('td')
            a = exp.find('a')
            if a:
                exps.append({"exp_id" : a.text.strip(), 
                             "labels" : [{"label" : label, "metadata" : {"text" : td[0].text.strip()} }] })
        return exps

    """
    experiment parsing when there are 3 columns in the html table
        param :
            rows : contains every row of the table
        return :
            list of the experiment ids with their labels
    """
    def find_experiments(self, rows) -> list:
            exps = []
            label_column_1 = rows[0].find('th').text.strip()
            label_column_2 = rows[0].find_all('th')[1].text.strip()
            for sequence in rows:
                a = sequence.find_all('a')
                if a :
                    data_column_1 = {"text" : sequence.find('td').text.strip()}
                    data_column_2 = {"text" : a[0].text.strip()}
                    html_text = HtmlProvider.retrieve_html_text(url_base = self.url, 
                                                                url = a[1].attrs['href'], 
                                                                files = self.files,
                                                                folder=self.folder)
                    if html_text != "":
                        soup = BeautifulSoup(html_text, 'html.parser')
                        try :
                            first_row = soup.find(text = "Experiment Name").parent.parent.parent
                            label_age = first_row.find_all('strong')[-1].text.strip()
                            for tr in first_row.find_next_siblings():
                                a = tr.find("a")
                                age = tr.find_all('td')[-1]
                                if a :
                                    exps.append({"exp_id" : a.text.strip(), 
                                        "labels" : [{"label" : label_column_1, "metadata" : data_column_1}, 
                                                    {"label" : label_column_2, "metadata" : data_column_2}, 
                                                    {"label" : label_age, "metadata" : {"age" : age.text.strip()}}
                                    ]})
                        except : 
                            Logger.console().warning(f"experiments of sequence {data_column_2} were not parsed")
            return exps    

    """
    retrieve the source of the html 
    reads the file in local or fetch the source if a url was given as a nimbus parameter
        param :
            url_base : the url given for the execution of nimbus
            url : url found in 3rd column
            files : file list (empty if url_base is not None)
        return :
            str : the html source code
    """
    @staticmethod
    def retrieve_html_text(url_base : str, url:str, files : list, folder:str = None) -> str:
        html_text = ""
        if url_base != None and len(files) == 0:
            try :
                url_parse = urlparse(url_base)._replace(path = url)
                req = requests.get(url_parse.geturl())
                if req.ok :
                    html_text = req.text
            except :
                Logger.console().warning(f"url {url} could not be accessed")
        else :

            new_url = url
            if not path.exists(url):
                if folder is not None :
                    new_url = path.join(folder, url if not url.startswith("/") else url[1:-1])
                else :
                    idx = files[0].find(url.split("/")[0])
                    if idx != -1:
                        new_url = path.join(files[0][0:idx], url if not url.startswith("/") else url[1:-1])

            if path.exists(new_url):
                html_text = codecs.open(url, "r",  encoding='utf-8', errors='ignore').read()
            else :                
                Logger.console().warning(f"local path {url} not found")
        return html_text        

    """
    build with local folder or file
        param :
            filepath : str
        return :
            HtmlProvider
    """
    @staticmethod
    def build(filepath : str, folder : str = None) -> 'HtmlProvider':
        blacklist = ("default_settings.dat")
        if path.isfile(filepath) and filepath.endswith("html"):            
            return HtmlProvider(files=[filepath], html_text = None, url = None, folder=folder)
        return HtmlProvider(
            files = [path.join(filepath, file.replace("dat","html")) for file in listdir(filepath) if file not in blacklist and file.endswith("dat")],
            html_text = None,
            url = None,
            folder=folder
        )    

    """
    build with url
        param :
            url : str
        return :
            HtmlProvider
    """
    @staticmethod
    def build_from_src(url : str) -> 'HtmlProvider':
        r = requests.get(url)
        res = None
        if r.ok :
            res = HtmlProvider(files = [], html_text = r.text, url = url)
        return res, r.ok