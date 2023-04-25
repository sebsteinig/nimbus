from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type
import numpy as np
from netCDF4 import Dataset,_netCDF4
import os.path as path
from os import remove
from cdo import Cdo
import sys
import variables.info as inf
from file_managers.output_folder import OutputFolder
from utils.logger import Logger,_Logger
from utils.metadata import Metadata
import json

class IncorrectVariable(Exception):pass
 
def iter(values:Tuple[Union[str,Set[str]]]):
    for value in values :
        if type(value) is str:
            yield value
        elif type(value) is set:
            yield from value
def csv(v):
    names = iter(v)
    return next(names) + "".join(f",{name}" for name in names)
def flatten(l):
    return [item for sublist in l for item in sublist]

def in_bounds(data, lb, ub):
    return np.nanmin(data) >= lb and np.nanmax(data) <= ub

cdo = Cdo()

@dataclass
class Variable:
    name : str
    look_for : Tuple[Union[Set[str],str]] = None
    preprocess : Callable[[Dict,Union[str,List[str]]],Union[str,List[str]]] = lambda x,y:y
    process : Callable[[List[np.ndarray]],np.ndarray] = lambda x:x


    def __clean_dimensions(self,variable:_netCDF4.Variable,dimensions:_netCDF4.Dimension, logger, info:inf.Info,dataset:_netCDF4.Dataset) -> np.ndarray:
        data = variable[:]
        metadata = Metadata(variableName=self.name, variable=variable)
        grid = info.get_grid(variable.dimensions)
        vertical = info.get_vertical(variable.dimensions)
        time = info.get_time(variable.dimensions)
        if grid is None:
            raise Exception("Could not find latitude and longitude")
        
        metadata.set_grid(grid)
        
        variable_dimensions = list(variable.dimensions)
        Logger.console().debug(f"variable_dimensions in clean dimension :\n{variable_dimensions}", "DIMENSION")
        Logger.console().debug(f"input in clean dimension :\n{data.shape}", "SHAPE")
        lon_index = variable_dimensions.index(grid.axis[0].name)
        lat_index = variable_dimensions.index(grid.axis[1].name)
        time_index = variable_dimensions.index(time.name)
        vertical_index = variable_dimensions.index(vertical.name)
        
        approved = [grid.axis[0].name,grid.axis[1].name]
        if time is not None:
            approved.append(time.name)
            metadata.set_time(time)
        if vertical is not None:
            approved.append(vertical.name)
            metadata.set_vertical(vertical)
        
        if time is not None and vertical is not None and time_index < vertical_index:
            variable_dimensions[vertical_index] = time.name
            variable_dimensions[time_index] = vertical.name
            data = np.swapaxes(data,time_index,vertical_index)
        
        if grid is not None and lon_index < lat_index:
            variable_dimensions[lon_index] = grid.axis[1].name
            variable_dimensions[lat_index] = grid.axis[0].name
            data = np.swapaxes(data,lon_index,lat_index)
            lon_index,lat_index = lat_index,lon_index

        lat_data = dataset.variables[grid.axis[1].name][:]
        lon_data = dataset.variables[grid.axis[0].name][:]
        
        if all(x<y for x, y in zip(lat_data, lat_data[1:])) :
            logger.warning("flip latitude of data", "FLIP")
            data = np.flip(data,lat_index)
    
        if not in_bounds(lat_data,-90,90):
            print(lat_data)
            raise Exception("Latitude should be between -90 and 90")
        
        if all(x>y for x, y in zip(lon_data, lon_data[1:])) and in_bounds(lat_data,-90,90):
            logger.warning("flip longitude of data", "FLIP")
            data = np.flip(data,lon_index)
        if not in_bounds(lon_data,-180,180):
            raise Exception("Longitude should be between -180 and 180")
    
        
        
        removed = [(i,name) for i,name in enumerate(variable.dimensions) \
            if not name in approved]
        removed.sort(reverse=True)
        for axis,name in removed:
            if dimensions[name].size == 1 :
                data = np.take(data,0,axis=axis)
            else :
                raise Exception(f"Unexpected dimension {name} of size {dimensions[name].size} > 1")
        
        if variable._FillValue is not None:
            threshold = int(np.log10(variable._FillValue))
            data[data>(10**threshold)] = np.nan
        Logger.console().debug(f"output in clean dimension :\n{data.shape}", "SHAPE")
        return data, metadata
    
    def select_grid(self,file:str,info:inf.Info):
        with Dataset(file,"r",format="NETCDF4") as dataset:
            variables = []
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            if self.look_for is None:
                if len(variable_names) != 1:
                    raise IncorrectVariable("Too many variables : must only be one variable if no names are specified")
                variable = dataset[list(variable_names)[0]]
                grid = info.get_grid(variable.dimensions)
            else :
                grids = []
                for possible_name in self.look_for:
                    if type(possible_name) is str:
                        if not possible_name in variable_names:
                            raise IncorrectVariable(f"No variables in {variable_names} match any of the specified name {name}")
                        variable = dataset[name]
                    elif type(possible_name) is set:
                        name = possible_name & variable_names  
                        if len(name) == 0:
                            raise IncorrectVariable(f"No variables match any of the specified names {variable_names}")
                        variable = dataset[list(name)[0]]
                    grids.append(info.get_grid(variable.dimensions))
                if len(set(grids)) != 1:
                    raise IncorrectVariable(f"All variable must in the same grid for the conversion")
                grid = grids[0]
        return grid
    
    
    def resize(self,resolution,file,grid,cdo):
        folder = path.dirname(file)
        resize_file_txt_name = path.basename(file).replace(".nc",".resize.txt")
        resize_file_txt_path = path.join(folder,resize_file_txt_name)
        #resize_file_nc_name = path.basename(file).replace(".nc",".resize.nc")
        #resize_file_nc_path = path.join(folder,resize_file_nc_name)
        Logger.console().debug(f"resize file : {resize_file_txt_path} , exist : {path.isfile(resize_file_txt_path)}", "RESOLUTION")
        
        griddes = {
            'gridtype'  : grid.category,
            'xsize'     : grid.points[1][0],
            'ysize'     : grid.points[1][1],
            'xfirst'    : grid.axis[0].bounds[0],
            'xinc'      : grid.axis[0].step,
            'yfirst'    : grid.axis[1].bounds[0],
            'yinc'      : grid.axis[1].step,
        }
        griddes['xsize'] = int(griddes['xsize']*resolution)
        griddes['ysize'] = int(griddes['ysize']*resolution)
        griddes['xinc'] = int(griddes['xinc']/resolution)
        griddes['yinc'] = int(griddes['yinc']/resolution)
        
        griddes_str = "".join(f"{key} = {value}\n" for key,value in griddes.items())
        
        with open(resize_file_txt_path,'w') as f:
            f.write(griddes_str)
        
        file = cdo.remapnn(resize_file_txt_path,input=file)
        remove(resize_file_txt_path)
        sinfo = cdo.sinfo(input=file)
        info = inf.Info.parse(sinfo)
        return file,info
    
    def __single_open(self,file:str,resolution:float,logger:_Logger) -> Tuple[List[np.ndarray],inf.Info]:
        sinfo = cdo.sinfo(input=file)
        Logger.console().debug(f"pre parsing :\n{sinfo}", "CDO INFO")
        info = inf.Info.parse(sinfo)
        logger.info(json.dumps(info.to_dict(),  indent = 2), "INFO")

        if resolution < 1  and resolution > 0:
            Logger.console().debug(f"Start resolution modification", "RESOLUTION")
            grid = self.select_grid(file, info)
            if grid.category != 'lonlat' :
                Logger.console().warning("can't change grid resolution, only lonlat grid are supported", "RESOLUTION")
            else :
                file,info = self.resize(resolution,file,grid,cdo)
        with Dataset(file,"r",format="NETCDF4") as dataset:
            variables = []
            metadatas = []
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            dimensions = dataset.dimensions
            if self.look_for is None:
                if len(variable_names) != 1:
                    raise IncorrectVariable("Too many variables : must only be one variable if no names are specified")
                variable = dataset[list(variable_names)[0]]
                variable, metadata = self.__clean_dimensions(variable,dimensions,logger, info,dataset)
                variables.append(variable)  
                metadatas.append(metadata)  
            else :
                for possible_name in self.look_for:
                    if type(possible_name) is str:
                        if not possible_name in variable_names:
                            raise IncorrectVariable(f"No variables in {variable_names} match any of the specified name {name}")
                        variable = dataset[possible_name]
                    elif type(possible_name) is set:
                        name = possible_name & variable_names  
                        if len(name) == 0:
                            raise IncorrectVariable(f"No variables match any of the specified names {variable_names}")
                        variable = dataset[list(name)[0]]
                    variable = self.__clean_dimensions(variable,dimensions,logger, info,dataset)
                    variables.append(variable)  
                    metadatas.append(metadata)                
        return self.process(variables), metadatas
        
    def __multi_open(self,inputs:list,resolution:float,logger:_Logger) -> List[Tuple[List[np.ndarray],inf.Info]]:
        variables = []
        for input in inputs :
            if type(input) is str:
                variables.extend(self.__single_open(input,resolution,logger))
            elif type(input) is list:
                variables.extend(self.__multi_open(input,resolution,logger))
        return variables
    
    @staticmethod
    def exec_preprocessing(files:list,selected_variable:str,output_dir:str,preprocess:Callable,inidata):
        output_files = []
        for input in files :
            output = path.join(output_dir,path.basename(input))
            preprocessed = preprocess(cdo,selected_variable,input,output,inidata)
            if type(preprocessed) is str:
                preprocessed = [preprocessed]
            output_files.append(preprocessed)
        return output_files
    
    def open(self,input:Union[str,List[str]],out_folder:OutputFolder,save:Callable[[List[str]],None],logger,resolution,inidata=None):
        selected_variable = csv(self.look_for)
        if type(input) is str:
            input = [input]
            
        output_dir = out_folder.tmp_nc()
        
        preprocessed_inputs = Variable.exec_preprocessing(input,selected_variable,output_dir,self.preprocess,inidata)
        preprocessed_inputs = save(preprocessed_inputs,resolution)
        
        output = []
        for preprocessed_input in preprocessed_inputs:
            if type(preprocessed_input) is str:
                output.append(self.__single_open(preprocessed_input,resolution,logger))
            elif type(preprocessed_input) is list:
                output.append(self.__multi_open(preprocessed_input,resolution,logger))
        return output
                

if __name__ == "__main__" :
    print("Cannot execute in main")
    import sys
    sys.exit(1)