import os
from utils.metadata import parser
from dotenv import dotenv_values
from utils.logger import Logger
import requests
from bs4 import BeautifulSoup
from typing import List

default_folder = os.path.join("papers")

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

def parse_html_publication(list_paths : List[str]):
    tags = {"Name" : "authors_short", "Title" : "title", 
            "Full Author List" : "authors_full", "Journal":"journal",
            "Year":"year", "Volume":"volume", "Pages":"pages", "DOI":"doi", 
            "Contact's Name":"owner_name", "Contact's email":"owner_email",
            "Abstract" : "abstract", "Brief Description" : "brief_desc"}
    parsed_data = []
    for path in list_paths:
        with open(path, "r") as f:
            data = parse_html(f.read(), tags)
            data["year"] = convert_to_int(data,"year", path)
            parsed_data.append(data)
    return parsed_data

                


def parse_dat_publication(list_paths):
    tags = ["title", "authors_short", "authors_full", "journal", "year", "volume", "pages",\
             "doi", "owner_name", "owner_email", "abstract", "brief_desc", "expts_paper", "expts_web"]
    res = []
    for path in list_paths:
        if path.endswith(".dat") :
            data = parser.bridge_parse({"abstract" : "", "brief_desc" : ""}, tags, path)
            data["year"] = convert_to_int(data,"year", path)
            res.append(data)
    return res

def convert_to_int(data, key, path):
    res = None
    if data.__contains__(key):
        value = data[key]
        if (value != None and value != "") and (value.upper() != "TBC" and value != "?") :
            try:
                res = int(value)
            except :
                Logger.console().warning(f"file {path} contains odd value for key {key}")
    return res

def post_publication(data:list):
    route = "insert/publication"
    config = dotenv_values(".env")
    url = f"{config['ARCHIVE_DB_URL']}/{route}"
    api_key = config['API_KEY']
    result = True
    _exp_ids = [publication["expts_web"] for publication in data]
    exp_ids = []
    for ids in _exp_ids:
        exp_ids.extend(ids)
    exp_ids = list(set(exp_ids))
    try :    
        res = requests.post(url,json={"publications":data,"exp_ids":exp_ids},cookies={"access_token":api_key})    
        if not res.ok:
            result = False
            print(res.status_code)
            print(res.text)
    except Exception as e:
        print(e)
        result = False
    return result

def add_publication(arg : str):
    blacklist = ("default_settings.dat")
    if not os.path.exists(arg):
        Logger.console().warning(f"{arg} path does not exist. Publication information will not be added to the database.")
        return 1
    if os.path.isfile(arg) and arg.endswith(".html") and os.path.exists(arg.removesuffix("html")+"dat"):
        data = parse_html_publication([arg])
    else :
        data = parse_html_publication([os.path.join(arg, p)for p in os.listdir(arg)\
                                       if p.endswith(".html") and os.path.exists(p.removesuffix("html")+"dat")])
    res = post_publication(data)
    if not res:
        Logger.console().warning("post failed")
        return 1
    return 0


if __name__ == "__main__" :
    pass