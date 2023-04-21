from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type
import numpy as np
from netCDF4 import Dataset,_netCDF4
import os
from cdo import Cdo
import sys
import variables.info as inf
from file_managers.output_folder import OutputFolder

class IncorrectVariable(Exception):pass
 
def iter(values:Tuple[Union[str,Set[str]]]):
    for value in values :
        match value :
            case value if type(value) is str:
                yield value
            case value if type(value) is set:
                yield from value
def csv(v):
    names = iter(v)
    return next(names) + "".join(f",{name}" for name in names)
def flatten(l):
    return [item for sublist in l for item in sublist]

def in_bounds(data, lb, ub):
    return np.nanmin(data) >= lb and np.nanmax(data) <= ub

@dataclass
class Variable:
    name : str
    look_for : Tuple[Union[Set[str],str]] = None
    preprocess : Callable[[Dict,Union[str,List[str]]],Union[str,List[str]]] = lambda x,y:y
    process : Callable[[List[np.ndarray]],np.ndarray] = lambda x:x


    def __clean_dimensions(self,variable:_netCDF4.Variable,dimensions:_netCDF4.Dimension,info:inf.Info,dataset:_netCDF4.Dataset) -> np.ndarray:
        data = variable[:]
    
        grid = info.get_grid(variable.dimensions)
        vertical = info.get_vertical(variable.dimensions)
        time = info.get_time(variable.dimensions)
        
        if grid is None:
            raise Exception("Could not find latitude and longitude")
        
        variable_dimensions = list(variable.dimensions)
        lon_index = variable_dimensions.index(grid.axis[0].name)
        lat_index = variable_dimensions.index(grid.axis[1].name)
        time_index = variable_dimensions.index(time.name)
        vertical_index = variable_dimensions.index(vertical.name)
        
        approved = [grid.axis[0].name,grid.axis[1].name]
        if time is not None:
            approved.append(time.name)
        if vertical is not None:
            approved.append(vertical.name)
        
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
            data = np.flip(data,lat_index)
        
        if not in_bounds(lat_data,-90,90):
            print(lat_data)
            raise Exception("Latitude should be between -90 and 90")
        
        if all(x>y for x, y in zip(lon_data, lon_data[1:])) and in_bounds(lat_data,-90,90):
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
        return data
      
    def __single_open(self,file:str) -> Tuple[List[np.ndarray],inf.Info]:
        cdo = Cdo()
        
        info = inf.Info.parse(cdo.sinfo(input=file))
        
        with Dataset(file,"r",format="NETCDF4") as dataset:
            variables = []
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            dimensions = dataset.dimensions
            if self.look_for is None:
                if len(variable_names) != 1:
                    raise IncorrectVariable("Too many variables : must only be one variable if no names are specified")
                variable = dataset[list(variable_names)[0]]
                variable= self.__clean_dimensions(variable,dimensions,info,dataset)
                variables.append(variable)
            else :
                for possible_name in self.look_for:
                    match possible_name:
                        case name if type(possible_name) is str:
                            if not name in variable_names:
                                raise IncorrectVariable(f"No variables match any of the specified names {names}")
                            variable = dataset[name]
                        case names if type(possible_name) is set:
                            name = names & variable_names  
                            if len(name) == 0:
                                raise IncorrectVariable(f"No variables match any of the specified names {names}")
                            variable = dataset[list(name)[0]]
                    variable = self.__clean_dimensions(variable,dimensions,info,dataset)
                    variables.append(variable)             
        return self.process(variables),info
        
    def __multi_open(self,inputs:list) -> List[Tuple[List[np.ndarray],inf.Info]]:
        variables = []
        for input in inputs :
            match input:
                case file if type(input) is str:
                    variables.extend(self.__single_open(file))
                case files if type(input) is list:
                    variables.extend(self.__multi_open(files))
        return variables
    
    @staticmethod
    def exec_preprocessing(files:list,selected_variable:str,output_dir:str,preprocess:Callable,inidata):
        cdo = Cdo()
        output_files = []
        for input in files :
            output = os.path.join(output_dir,os.path.basename(input))
            preprocessed = preprocess(cdo,selected_variable,input,output,inidata)
            if type(preprocessed) is str:
                preprocessed = [preprocessed]
            output_files.append(preprocessed)
        return output_files
    
    def open(self,input:Union[str,List[str]],out_folder:OutputFolder,save:Callable[[List[str]],None],inidata=None):
        selected_variable = csv(self.look_for)
        
        if type(input) is str:
            input = [input]
            
        output_dir = out_folder.tmp_nc()
        
        preprocessed_inputs = Variable.exec_preprocessing(input,selected_variable,output_dir,self.preprocess,inidata)
        preprocessed_inputs = save(preprocessed_inputs)
        
        output = []
        for preprocessed_input in preprocessed_inputs:
            match preprocessed_input:
                case file if type(preprocessed_input) is str:
                    output.append(self.__single_open(file))
                case files if type(preprocessed_input) is list:
                    output.append(self.__multi_open(files))
        return output
                

if __name__ == "__main__" :
    print("Cannot execute in main")
    import sys
    sys.exit(1)