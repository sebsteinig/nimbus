from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type
import numpy as np
from netCDF4 import Dataset,_netCDF4
import os
from cdo import Cdo
import sys
import variables.info as inf

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

@dataclass
class Variable:
    name : str
    look_for : Tuple[Union[Set[str],str]] = None
    preprocess : Callable[[Dict,Union[str,List[str]]],Union[str,List[str]]] = lambda x,y:y
    process : Callable[[List[np.ndarray]],np.ndarray] = lambda x:x


    def __clean_dimensions(self,variable:_netCDF4.Variable,dimensions:_netCDF4.Dimension,info:inf.Info) -> np.ndarray:
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
            data = np.swapaxes(data,time_index,vertical_index)
            
        
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
            data[data>threshold] = np.nan
        return data

    def __single_open(self,file:str) -> List[List[np.ndarray]]:
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
                variable= self.__clean_dimensions(variable,dimensions,info)
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
                    variable = self.__clean_dimensions(variable,dimensions,info)
                    variables.append(variable)             
        return self.process(variables)
        
    def __multi_open(self,inputs:list) -> List[List[np.ndarray]]:
        variables = []
        for input in inputs :
            match input:
                case file if type(input) is str:
                    variables.extend(self.__single_open(file))
                case files if type(input) is list:
                    variables.extend(self.__multi_open(files))
        return variables
    
    @staticmethod
    def exec_preprocessing(files:list,selected_variable:str,output_dir:str,preprocess:Callable,extra:dict):
        cdo = Cdo()
        output_files = []
        for input in files :
            #name = os.path.splitext(os.path.basename(input))[0]
            output = os.path.join(output_dir,os.path.basename(input))
            preprocessed = preprocess(cdo,selected_variable,input,output,extra)
            if type(preprocessed) is str:
                preprocessed = [preprocessed]
            output_files.append(preprocessed)
        return output_files
    
    def open(self,input:Union[str,List[str]],args:dict,save:Callable[[List[str]],None]) -> List[np.ndarray]:
        selected_variable = csv(self.look_for)
        
        if type(input) is str:
            input = [input]
        output_dir = args["env"].path_tmp_netcdf(args["expId"],"")
        
        preprocessed_inputs = Variable.exec_preprocessing(input,selected_variable,output_dir,self.preprocess,args)
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