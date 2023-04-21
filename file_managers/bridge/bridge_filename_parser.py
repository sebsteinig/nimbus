import numpy as np
from netCDF4 import Dataset
from dataclasses import dataclass
from enum import Enum,auto
from typing import Tuple,Union
import re
import os.path as path

@dataclass(eq=True, frozen=True)
class ExpId:
    name:str

class ParsingError(Exception):pass

class Realm(Enum):
    Athmosphere = 'a'
    Ocean = 'o'
    
@dataclass(eq=True, frozen=True)
class OutputStream:
    category:str
    
class Statistic(Enum):
    TimeMean = "cl"
    StandardDeviation = "sd"
@dataclass(eq=True, frozen=True)
class Annual:
    value = "ann"
    def key(self):
        return len(Month)+len(Season)
class Month(Enum):
    Jan="jan"
    Feb="feb"
    Mar="mar"
    Apr="apr"
    May="may"
    Jun="jun"
    Jul="jul"
    Aug="aug"
    Sep="sep"
    Oct="oct"
    Nov="nov"
    Dec="dec"
    def key(self):
        return Month._member_names_.index(self.name)
    
class Season(Enum):
    Djf = "djf"
    Mam = "mam"
    Jja = "jja"
    Jjs = "jjs"
    Son = "son"
    def key(self):
        return len(Month) + Season._member_names_.index(self.name)


@dataclass(eq=True, frozen=True)
class AvgPeriod:
    mean:Union[Annual,Month,Season]

@dataclass(eq=True, frozen=True)
class BridgeName:
    expId:ExpId
    realm:Realm
    output_stream:OutputStream
    statistic:Statistic
    avg_period:AvgPeriod
    filepath:str
    
def ruleExpID(filename:str,cursor:int):
    if match := re.match("^[a-zA-Z]{5}\d?",filename[cursor:]):
        return ExpId(match.group(0)),cursor+match.span()[1]
    return None
        

def ruleRealm(filename:str,cursor:int):
    if filename[cursor] in Realm._value2member_map_:
        return Realm._value2member_map_[filename[cursor]],cursor+1

def ruleOutputStream(filename:str,cursor:int):
    if match := re.match("^[a-zA-Z]{2}",filename[cursor:]):
        return OutputStream(match.group(0)),cursor+match.span()[1]
    return None

def ruleStatistic(filename:str,cursor:int):
    if filename[cursor:cursor+2] in Statistic._value2member_map_:
        return Statistic._value2member_map_[filename[cursor:cursor+2]],cursor+2

def ruleAvgPeridod(filename:str,cursor:int):
    if match := re.match("^ann",filename[cursor:]):
        return AvgPeriod(Annual()),cursor+match.span()[1]
    if filename[cursor:cursor+3] in Month._value2member_map_:
        return AvgPeriod(Month._value2member_map_[filename[cursor:cursor+3]]),cursor+3
    if filename[cursor:cursor+3] in Season._value2member_map_:
        return AvgPeriod(Season._value2member_map_[filename[cursor:cursor+3]]),cursor+3
    return None

def eatdot(filename:str,cursor:int):
    if filename[cursor] == '.':
        return cursor +1
    return cursor

def parse(filepath:str):
    filename = path.basename(filepath)
    cursor = 0
    if not (res := ruleExpID(filename,cursor)):
        raise ParsingError(f"invalid experience id for {filename} in {filepath}")
    expId,cursor =res
    if not (res := ruleRealm(filename,cursor)):
        raise ParsingError(f"invalid realm for {filename} in {filepath}")
    realm,cursor =res
    cursor = eatdot(filename,cursor)
    if not (res := ruleOutputStream(filename,cursor)):
        raise ParsingError(f"invalid output stream for {filename} in {filepath}")
    output_stream,cursor =res
    if not (res := ruleStatistic(filename,cursor)):
        raise ParsingError(f"invalid statistic for {filename} in {filepath}")
    statistic,cursor =res
    if not (res := ruleAvgPeridod(filename,cursor)):
        raise ParsingError(f"invalid averaging period for {filename} in {filepath}")
    avg_period,cursor =res
    return BridgeName(expId=expId,realm=realm,\
        output_stream=output_stream,\
        statistic=statistic,\
        avg_period=avg_period,\
        filepath=filepath)
    


def test():
    print(parse("texpa1a.pccljun.nc"))

if __name__ == "__main__":
    test()