from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type
import numpy as np
from netCDF4 import Dataset,_netCDF4
import os.path as path
from os import remove
from cdo import Cdo
import sys
from utils.config import Config
import utils.variables.info as inf
from utils.logger import Logger,_Logger
from utils.metadata import Metadata

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

conversion_prefixe = {"m":10e-3,"c":10e-2,"d":10e-1,"":1,"da":10,"h":10e2,"k":10e3}

def convert_unit(levels,from_unit,to_unit):
    if from_unit is None:
        return levels
    if from_unit == to_unit:
        return levels
    if "Pa"  in to_unit:
        if "bar" in from_unit:
            rate = 100000
            from_exp = conversion_prefixe[from_unit.replace("bar",'')]
            to_exp = conversion_prefixe[to_unit.replace("Pa",'')]
            return [l*from_exp*rate/to_exp for l in levels]
            
    
    raise Exception(f"UNIMPLMENTED : can't convert from {from_unit} to {to_unit}")

@dataclass(eq=True, frozen=True)
class Variable:
    name : str
    realm : str
    preprocess : Callable
    process : Callable[[List[np.ndarray]],List[np.ndarray]] 


def clean_dimensions(variable:_netCDF4.Variable,dimensions:_netCDF4.Dimension, logger:_Logger, info:inf.Info,dataset:_netCDF4.Dataset) -> np.ndarray:
    data = variable[:]

    grid = info.get_grid(variable.dimensions)
    vertical = info.get_vertical(variable.dimensions)
    time = info.get_time(variable.dimensions)
    if grid is None:
        raise Exception("Could not find latitude and longitude")
    
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
        logger.warning("flip latitude of data", "FLIP")
        data = np.flip(data,lat_index)

    if not in_bounds(lat_data,-90,90):
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
    return data


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

    
def resize(resolution,file,grid,cdo):
    lb,ub = abs(resolution[0]),abs(resolution[1])
    folder = path.dirname(file)
    resize_file_txt_name = path.basename(file).replace(".nc",".resize.txt")
    resize_file_txt_path = path.join(folder,resize_file_txt_name)
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
    new_xinc = -lb if grid.axis[0].bounds[1] < griddes['xfirst'] else lb
    new_yinc = -ub if grid.axis[1].bounds[1] < griddes['yfirst'] else ub
    griddes['xsize'] = int(griddes['xsize'] * griddes['xinc'] / new_xinc)
    griddes['ysize'] = int(griddes['ysize'] * griddes['yinc'] / new_yinc)
    griddes['xinc'] = new_xinc
    griddes['yinc'] = new_yinc
    griddes_str = "".join(f"{key} = {value}\n" for key,value in griddes.items())
    
    with open(resize_file_txt_path,'w') as f:
        f.write(griddes_str)
    
    res_suffixe = f".rx{griddes['xinc']}.ry{griddes['yinc']}"
    output_file = file.replace(".nc",f"{res_suffixe}.nc")
    file = cdo.remapnn(resize_file_txt_path,input=file,output=output_file)
    remove(resize_file_txt_path)
    sinfo = cdo.sinfo(input=output_file)
    info = inf.Info.parse(sinfo)
    return output_file,info

def select_levels(variable:Variable,config:Config,file,vertical):
    
    if variable.realm is None:
        return file
    realm = config.get_realm_hp(variable)
    levels,unit = realm["levels"],realm["unit"]

    levels = convert_unit(levels,vertical.unit,unit)
    
    epsilons = {}
    for i,l in enumerate(levels):
        if i == 0:
            e1 = (abs(levels[i+1]-l)*0.25)
            e2 = e1
        elif i == len(levels) - 1:
            e1 = (abs(levels[i-1]-l)*0.25)
            e2 = e1
        else :
            e2 = (abs(levels[i+1]-l)*0.25)
            e1 = (abs(levels[i-1]-l)*0.25)
        epsilons[l] = (e1,e2)
        
    
    with Dataset(file,"r",format="NETCDF4") as dataset:
        file_levels = [ float(f) for f in (dataset[vertical.name][:])]
    
    distance = { level:[(i,abs(level-l)) for i,l in enumerate(file_levels) if (l >= level - epsilons[level][0]) and (l <= level + epsilons[level][1])]   for level in levels}
    distance_index = {}
    for level,d in distance.items():
        if len(d) > 0:
            unzipped = list(zip(*d))
            unzipped_d,unzipped_i = unzipped[1], unzipped[0]
            distance_index[level] = unzipped_i[np.argmin(unzipped_d)]
            
    
    index = list(distance_index.values())
    index_str ="".join(f",{i+1}" for i in index )
    
    output_file = file.replace(".nc",".zr.nc")
    cdo.sellevidx(index_str,input=file, output=output_file)
    return output_file

def retrieve_from_nc_files(variable:Variable,file:str,var_name:str,hyper_parameters:dict,config:Config,metadata:Metadata) -> Tuple[np.ndarray,inf.Info]:
    sinfo = cdo.sinfo(input=file)
    info = inf.Info.parse(sinfo)
    
    grid,vertical = select_grid_and_vertical(file=file, info=info,var_name=var_name)
    
    original_grid_type = grid.category
    original_xsize = grid.points[1][0]
    original_ysize = grid.points[1][1]
    original_xinc = grid.axis[0].step
    original_yinc = grid.axis[1].step
    
    if hyper_parameters['resolution'][0] is not None  and hyper_parameters['resolution'][1] is not None:
        Logger.console().debug(f"Start resolution modification", "RESOLUTION")
        if grid.category != 'lonlat' :
            Logger.console().warning("can't change grid resolution, only lonlat grid are supported", "RESOLUTION")
        else :
            file,info = resize(hyper_parameters['resolution'],file,grid,cdo)
    
    if vertical is not None and vertical.levels is not None and vertical.levels > 1:
        Logger.console().debug(f"Start levels selection", "LEVEL")
        file = select_levels(variable,config,file,vertical)
        sinfo = cdo.sinfo(input=file)
        info = inf.Info.parse(sinfo)
    
    with Dataset(file,"r",format="NETCDF4") as dataset:
        dimensions = dataset.dimensions        
        if var_name is None:
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            var_name = list(variable_names)[0]
        __variable = dataset[var_name]
        
        metadata.extends(**info.reduce(__variable.dimensions).to_metadata())

        metadata.extends_for(var_name,\
            original_variable_name = "" if 'name'  not in __variable.__dict__ else __variable.name,\
            original_variable_long_name = "" if 'long_name' not  in __variable.__dict__ else __variable.long_name,\
            std_name = "" if 'standard_name' not in __variable.__dict__ else __variable.standard_name,\
            model_name  = "",\
            variable_unit  =  "" if 'units' not  in __variable.__dict__ else  __variable.units,\
            history = "" if 'history' not  in dataset.__dict__ else str(dataset.history),\
            original_variable_unit  = "" if 'units' not  in __variable.__dict__ else  __variable.units)
        metadata.extends_for(var_name,\
            original_grid_type = original_grid_type,\
            original_xsize = original_xsize,\
            original_ysize = original_ysize,\
            original_yinc = original_yinc,\
            original_xinc = original_xinc)
        np_array = clean_dimensions(__variable,dimensions,hyper_parameters['logger'], info,dataset)
    
    return np_array
        
    
def retrieve_data(inputs:List[Tuple[str,str]],variable:Variable,hyper_parameters:dict,config:Config,save:Callable) -> List[Tuple[np.ndarray,inf.Info]]:
    np_arrays = []
     
    inputs = variable.preprocess(inputs=inputs,\
        output_directory=hyper_parameters["tmp_directory"])
    inputs = save(inputs)
    
    metadata = Metadata()
    metadata.extends(variable_name=variable.name,\
        resolution=hyper_parameters['resolution'],\
        threshold=config.get_hp(variable.name).threshold
    )
    for input_file,var_name in inputs:
        Logger.console().debug(f"Converting {input_file} for variable {var_name} ...","CONVERSION")
        np_arrays.append(\
            retrieve_from_nc_files(\
                variable=variable,\
                file=input_file,\
                var_name=var_name,\
                hyper_parameters=hyper_parameters,\
                config=config,\
                metadata = metadata)
            )
    return variable.process(np_arrays),metadata


if __name__ == "__main__" :
    print("Cannot execute in main")
    import sys
    sys.exit(1)