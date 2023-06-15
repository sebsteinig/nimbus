from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type
import numpy as np
from netCDF4 import Dataset,_netCDF4
from cdo import Cdo
import sys
from utils.config import Config
import utils.variables.info as inf
from utils.logger import Logger,_Logger
from utils.metadata.metadata import Metadata, VariableSpecificMetadata
from utils.variables.pipelines.horizontal_pipeline import HorizontalPipeline
from utils.variables.pipelines.vertical_pipeline import VerticalPipeline
from utils.variables.pipelines.cleaning_pipeline import CleaningPipeline
import os.path as path
from os import link

cdo = Cdo()

@dataclass(eq=True, frozen=True)
class Variable:
    name : str
    realm : str
    preprocess : Callable
    process : Callable[[List[np.ndarray]],List[Tuple[List[np.ndarray],str]]] 

def select_grid_and_vertical(file:str,var_name:str,info:inf.Info):
    with Dataset(file,"r",format="NETCDF4") as dataset:
        variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())

        if var_name is None:
            var_name = list(variable_names)[0]
        
        if var_name not in variable_names:
            raise Exception(f"{var_name} not in file : {file}")
        
        variable = dataset[var_name]
        grid = info.get_grid(variable.dimensions)
        vertical = info.get_vertical(variable.dimensions)
    return grid,vertical


def load(variable:Variable,file:str,var_name:str,hyper_parameters:dict,config:Config,metadata:Metadata) -> Tuple[np.ndarray,inf.Info]:
    sinfo = cdo.sinfo(input=file)
    info = inf.Info.parse(sinfo)
    vs_metadata = VariableSpecificMetadata()
    
    grid,vertical = select_grid_and_vertical(file=file, info=info,var_name=var_name)
    vs_metadata.extends(
        original_grid_type = grid.category,\
        original_xsize = grid.points[1][0],\
        original_ysize = grid.points[1][1],\
        original_yinc = grid.axis[1].step,\
        original_xinc = grid.axis[0].step)

    
    file,info = HorizontalPipeline.build(
        resolution=hyper_parameters['resolution'],\
        grid=grid)\
    .exec(file,info)
    
    file,info = VerticalPipeline.build(variable=variable,\
        vertical=vertical,\
        config = config)\
    .exec(file,info)
    
    with Dataset(file,"r",format="NETCDF4") as dataset:
        if var_name is None:
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            var_name = list(variable_names)[0]
        __variable = dataset[var_name]
        
        metadata.extends(**info.reduce(__variable.dimensions).to_metadata())

        vs_metadata.extends(
            original_variable_name = "" if 'name'  not in __variable.__dict__ else __variable.name,\
            original_variable_long_name = "" if 'long_name' not  in __variable.__dict__ else __variable.long_name,\
            std_name = "" if 'standard_name' not in __variable.__dict__ else __variable.standard_name,\
            model_name  = "",\
            variable_unit  =  "" if 'units' not  in __variable.__dict__ else  __variable.units,\
            history = "" if 'history' not  in dataset.__dict__ else str(dataset.history),\
            original_variable_unit  = "" if 'units' not  in __variable.__dict__ else  __variable.units)
        
        np_array = CleaningPipeline.build(dataset=dataset,\
            info=info,\
            logger=hyper_parameters['logger'],
            var_name=var_name
        ).exec()
           
    return np_array,vs_metadata

class VariableNotFoundError(Exception):pass


def memoize(f):
    cache = {}
    def memoized(inputs:List[Tuple[str,str]],variable:Variable,tmp_directory:str,cluster):
        file = None
        for _file,var in inputs:
            if _file in cluster:
                file = _file
                break
        if file is not None:
            real,vars = cluster[file]
            
            if real in cache:
                outputs = cache[real]
                return [(outputs,var) for file,var in inputs]
            else :
                modified_inputs = [(file,",".join(vars))]
                outputs = f(modified_inputs,variable,tmp_directory,cluster)
                cache[real] = outputs[0][0]
                return [(outputs[0][0],var) for file,var in inputs]
        else :
            return f(inputs,variable,tmp_directory,cluster)
    return memoized
        

@memoize
def preprocess(inputs:List[Tuple[str,str]],variable:Variable,tmp_directory:str,cluster):
    for input_file,var_name in inputs:
        if "," in var_name:
            var_name = var_name.split(",")
        else :
            var_name = [var_name]
        with Dataset(input_file,"r",format="NETCDF4") as dataset:
            if any(name not in dataset.variables for name in var_name):
                raise VariableNotFoundError(var_name)
     
    inputs = variable.preprocess(inputs=inputs,\
        output_directory=tmp_directory) 
    return inputs

"""
    retrieve data with the corresponding metadata from a list files and variable name
    param :
        inputs:List[Tuple[str,str]]
        variable:Variable
        hyper_parameters:dict
        config:Config
        output_file:str
        save:Callable
    return :
        Tuple[List[Tuple[List[np.ndarray],str]],Metadata]
"""   
def retrieve_data(inputs:List[Tuple[str,str]],variable:Variable,hyper_parameters:dict,config:Config,output_file:str,save:Callable) -> Tuple[List[Tuple[List[np.ndarray],str]],Metadata]:
    np_arrays_vs_metadata = []
     
    #inputs = save(inputs)
    
    metadata = Metadata()
    metadata.extends(variable_name=variable.name,\
        resolution=hyper_parameters['resolution'],\
        threshold=config.get_hp(variable.name).threshold
    )
    for input_file,var_name in inputs:
        Logger.console().debug(f"Converting {input_file} for variable {var_name} ...","CONVERSION")
        np_array,vs_metadata = load(\
                variable=variable,\
                file=input_file,\
                var_name=var_name,\
                hyper_parameters=hyper_parameters,\
                config=config,\
                metadata = metadata)
        np_arrays_vs_metadata.append((np_array,vs_metadata))
    return variable.process((np_arrays_vs_metadata,output_file)),metadata


if __name__ == "__main__" :
    print("Cannot execute in main")
    import sys
    sys.exit(1)