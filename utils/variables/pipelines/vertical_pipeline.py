from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from utils.logger import Logger
from utils.config import Config
from utils.variables.info import Info, Vertical
from netCDF4 import Dataset,_netCDF4
from utils.import_cdo import cdo

EPSILON = 0.25

@dataclass
class UnitConverter:
    rate:float
    from_exp:float
    to_exp:float
    PREFIXES = {
        "m":10e-3,
        "c":10e-2,
        "d":10e-1,
        "":1,
        "da":10,
        "h":10e2,
        "k":10e3
    }
    
    UNITS_RATE = {
        ("Pa","bar") : 1e-5,
        ("bar","Pa") : 1e5,
        ("bar","bar") : 1,
        ("Pa","Pa") : 1,
        ("m","m") : 1,
    }
    SUPPORTED_UNITS = (lambda x,y: set(x) | set(y))(*zip(*UNITS_RATE.keys()))
    
    """
        convert values to an other unit
        param :
            values : np.ndarray
        return :
            np.ndarray
    """
    def convert(self,values:np.ndarray) -> np.ndarray:
        return values * self.from_exp *self.rate/self.to_exp 
    
    """
        find the exponent of a given unit
        param :
            unit : str
        return :
            Tuple[str,str]
    """
    @staticmethod
    def find_exp(unit):
        return next(\
            ((unit.replace(name,''),name) for name in UnitConverter.SUPPORTED_UNITS\
                if name in unit and unit.endswith(name))\
            ,None)
        
    """
        build a unit converter between the given unitss
        param :
            from_unit : str,
            to_unit : str
        return :
            UnitConverter
    """
    @staticmethod
    def build(from_unit,to_unit) -> 'UnitConverter':
        if from_unit is None or from_unit == to_unit :
            class IDLE:
                def convert(self,values:list) -> list:
                    return values
            return IDLE()
        
        to_exp,to_unit = UnitConverter.find_exp(to_unit)
        from_exp,from_unit = UnitConverter.find_exp(from_unit)
        if to_exp is None or from_exp is None:
            raise Exception(f"UNIMPLMENTED : can't convert from {from_unit} to {to_unit}")
        if to_exp not in UnitConverter.PREFIXES or from_exp not in UnitConverter.PREFIXES:
            raise Exception(f"UNIMPLMENTED : can't convert with {from_exp} to {to_exp}")
         
        return UnitConverter(rate = UnitConverter.UNITS_RATE[(from_unit,to_unit)],\
            from_exp = UnitConverter.PREFIXES[from_exp],\
            to_exp = UnitConverter.PREFIXES[to_exp],\
        )
            
                
        

@dataclass
class VerticalPipeline:
    desired_unit :str
    desired_levels : List[float]
    vertical_unit : str
    vertical_name : str
    
    
    """
        execute the pipeline, retrieving the vertical levels of the given file,
        converting these levels to the desired unit, evaluate the distances between the desired levels
        and the file levels, selecting the indexes of the closest levels from the desired levels,
        then selecting with cdo the levels and output them in a file
        param :
            file : str
            info : Info
        return :
            Tuple[str,Info]
    """
    def exec(self,file:str,info:Info) -> Tuple[str,Info]:
        
        with Dataset(file,"r",format="NETCDF4") as dataset:
            file_levels = dataset[self.vertical_name][:]
        
        converter = UnitConverter.build(\
            from_unit = self.vertical_unit,\
            to_unit = self.desired_unit)
        
        file_levels = converter.convert(file_levels)
        
        distances = self.eval_distances(file_levels)
        
        selected_indexes = self.select_indexes(distances)
        
        output_file = file.replace(".nc",".zr.nc")
        cdo.sellevidx(selected_indexes,input=file, output=output_file)
        
        sinfo = cdo.sinfo(input=output_file)
        info = Info.parse(sinfo)
        
        return output_file,info
    
    """
        selecting the indexes of the closest levels
        param :
            distances : list
        return :
            str
    """
    def select_indexes(self,distances:list) -> str :
        indexes = []
        for closest_levels in distances:
            
            closest_levels_indexes = list(closest_levels.keys())
            closest_levels_distances = list(closest_levels.values())
            if len(closest_levels_distances) > 0:
                indexes.append(closest_levels_indexes[np.argmin(closest_levels_distances)])
        
        return "".join(f",{i+1}" for i in indexes )
        
        
    """
        evaluate the distances between the file levels and the desired levels
        param :
            file_levels : List[float]
        return :
            list 
    """
    def eval_distances(self,file_levels:List[float]) -> list: 
        epsilons = self.epsilons(self.desired_levels)    
        distances = []
        for desired_level in self.desired_levels :
            closest_levels = {}
            for index,level in enumerate(file_levels):
                
                if (level >= desired_level - epsilons[desired_level][0]) \
                    and (level <= desired_level + epsilons[desired_level][1]):
                        
                    closest_levels[index] = abs(desired_level - level)
                    
            distances.append(closest_levels)
        return distances
    
    def epsilons(self,levels) : 
        epsilons = {}
        epsilons[levels[0]] = [abs(levels[0])*EPSILON,abs(levels[1]-levels[0])*EPSILON]
        for index in range(1,len(levels)-1):
            epsilons[levels[index]] = [
                abs(levels[index - 1] - levels[index]) * EPSILON ,\
                abs(levels[index + 1] - levels[index]) * EPSILON ,\
            ]
        epsilons[levels[-1]] = [abs(levels[-2]-levels[-1])*EPSILON, abs(levels[-1])*EPSILON]
        return epsilons
    
    """
        build a vertical pipeline with the correct info,
        if no pipeline is needed, return a idle object that does nothing
        param :
            variable,
            vertical : Vertical,
            config : Config
        return :
            VerticalPipeline
    """
    @staticmethod
    def build(variable,vertical:Vertical,config:Config) -> 'VerticalPipeline':
        
        if  variable.realm is None or\
            vertical.unit is None or\
            vertical is  None or\
            vertical.levels is  None or\
            vertical.levels <= 1:
            class IDLE:
                def exec(self,file:str,info:Info) -> Tuple[str,Info]:
                    return file,info
            return IDLE()
        realm = config.get_realm_hp(variable)
        levels,unit = realm["levels"],realm["unit"]
        return VerticalPipeline(desired_unit=unit,\
            desired_levels=levels,\
            vertical_name=vertical.name,\
            vertical_unit= vertical.unit)
        
