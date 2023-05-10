from typing import Tuple
from utils.variables.info import Info
from dataclasses import dataclass
import numpy as np
from utils.logger import _Logger

@dataclass
class DataAxis:
    data:np.ndarray
    index : int
    size : int
    """
        check if the axis is between the given bounds ( -90,90 for latitude and -180,180 for longitude)
        and check if the data if stricly increasing or decreasing and flip otherwise
        param :
            bounds : Tuple[int,int],
            data : np.ndarray,
            logger : _Logger,
            increasing : bool = True by default
        return :
            np.ndarray
    """
    def flip(self,bounds : Tuple[int,int], data : np.ndarray,logger,increasing = True) -> np.ndarray :
        if not (np.nanmin(self.data) >= bounds[0] and np.nanmax(self.data) <= bounds[1]):
            raise Exception(f"Axis should be between {bounds[0]} and {bounds[1]}")
            
        if increasing:
            if not np.any(self.data[:-1] < self.data[1:]) :
                logger.warning("flip axis of data", "FLIP")
                return np.flip(data,self.index)
            return data
        else :
            if not np.any(self.data[:-1] > self.data[1:]) :
                logger.warning("flip axis of data", "FLIP")
                return np.flip(data,self.index)
            return data
            
 
@dataclass               
class CleaningPipeline:
    logger : _Logger
    data : np.ndarray
    latitude : DataAxis
    longitude : DataAxis
    time : DataAxis
    vertical : DataAxis
    """
        execute cleaning pipeline :
            - flip the latitude if needed
            - flip the longitude if needed
            - reorder the shape of the data to correspond to (vertical,time,latitude,longitude)
        param :
            
        return :
            np.ndarray
    """
    def exec(self) -> np.ndarray :
        data = self.latitude.flip((-90,90),self.data,self.logger,increasing=False)
        data = self.longitude.flip((-180,180),data,self.logger,increasing=True)
        data = self.reorder(data)
        
        return data
    """
        reorder the data to correspond to (vertical,time,latitude,longitude)
        param :
            data : np.ndarray
        return :
            np.ndarray
    """
    def reorder(self,data:np.ndarray) -> np.ndarray:
        if self.time.index is not None and self.vertical.index is not None and self.time.index < self.vertical.index :
            data = np.swapaxes(data , self.time.index , self.vertical.index)
        if self.longitude.index < self.latitude.index :
            data = np.swapaxes(data , self.longitude.index , self.latitude.index)
        return data
    
    """
        remove unnecessary dimensions from data, raise exception if the removed dimensions contained something
        param :
            dataset,
            approved,
            variable,
        return :
            np.ndarray 
    """
    @staticmethod
    def clean(dataset,approved,variable,data) -> np.ndarray:
        black_list = ((i,dim) for i,dim in enumerate(variable.dimensions) if dim not in approved )
        for i,rejected in black_list:
            if dataset.dimensions[rejected].size == 1 :
                data = np.take(data,0,axis=i)
            else :
                raise Exception(f"Unexpected dimension {rejected} of size {dataset.dimensions[rejected].size} > 1")
        return data
    """
        set all value that are above the fillvalue to nan
        param :
            fillvalue
        return :
            np.ndarray
    """
    @staticmethod
    def threshold(fillvalue,data) -> np.ndarray:
        if fillvalue is not None:
            threshold = int(np.log10(fillvalue))
            data[data>(10**threshold)] = np.nan
        return data
    
    """
        build a cleaning pipeline with the correct input
        param :
            dataset,
            info,
            var_name,
            logger
        return :
            CleaningPipeline
    """
    @staticmethod
    def build(dataset,info:Info,var_name:str,logger:_Logger) -> 'CleaningPipeline':
        variable = dataset.variables[var_name]
        data = variable[:]
        
        grid = info.get_grid(variable.dimensions)
        vertical = info.get_vertical(variable.dimensions)
        time = info.get_time(variable.dimensions)
        
        if grid is None:
            raise Exception("Could not find latitude and longitude")
        
        
        variable_dimensions = list(variable.dimensions)
            
        lon_index = variable_dimensions.index(grid.axis[0].name)
        lat_index = variable_dimensions.index(grid.axis[1].name)
        
        approved = [grid.axis[0].name , grid.axis[1].name]
        
        if time is not None:
            time_index = variable_dimensions.index(time.name)
            time_size = time.step
            approved.append(time.name)
        else :
            time_index = None
            time_size = 1
            
        if vertical is not None :
            vertical_index = variable_dimensions.index(vertical.name)
            vertical_size = vertical.levels
            approved.append(vertical.name)
        else :
            vertical_index = None
            vertical_size = 1
        
        data = CleaningPipeline.clean(dataset,approved,variable,data)
        data = CleaningPipeline.threshold(variable._FillValue,data)
            
        return CleaningPipeline(
            logger=logger,\
            data = data,\
            latitude = DataAxis(data = dataset.variables[grid.axis[1].name],\
                index= lat_index,\
                size = grid.points[1][1]),\
            longitude = DataAxis(data = dataset.variables[grid.axis[0].name],\
                index= lon_index,\
                size = grid.points[1][0]),\
            time = DataAxis(data = None,\
                index= time_index,\
                size = time_size),\
            vertical = DataAxis(data = None,\
                index= vertical_index,\
                size = vertical_size),\
        )