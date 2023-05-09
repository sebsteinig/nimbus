from dataclasses import dataclass
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import warnings
import os
import json
from datetime import datetime
from utils.metadata import Metadata,VariableSpecificMetadata
from utils.logger import Logger,_Logger
from typing import List, Tuple, Dict
from enum import Enum

class TooManyInputs(Exception):pass
class LongitudeLatitude(Exception):pass
class IncorrectInputTypes(Exception): pass
class IncorrectInputDim(Exception) : pass
class IncorrectNumberOfVariables(Exception) : pass
class IncorrectInputSize(Exception) : pass

class Mode(Enum):
    L = 1
    RGB = 3
    RGBA = 4

@dataclass
class Shape:
    level:int
    time:int
    lat:int
    lon:int

"""
    function that replaces nan values with 255in the output.
    param :
        output : ndarray
    return :
        ndarray
"""
def clean(output : np.ndarray) -> np.ndarray:
    output[np.isnan(output)] = 255
    return output.clip(0,254)

"""
    transform a Metadata instance into a PngInfo.
    param :
        metadata : Metadata
    return :
        PngInfo
"""
def to_png_info(metadata : Metadata):
    png_info = PngInfo()
    for key,value in metadata.to_dict().items():
        png_info.add_text(key,str(json.dumps(value)))
    return png_info

"""
    save the png image
    param :
        output : ndarray
        output_file : str (name of the image file)
        directory : str (name of the ouput directory)
        metadata : PngInfo
        mode : str (L or RGB or RGBA)
    return :
        str (the path to the output image)
"""
def save(output : np.ndarray, output_file : str, directory :str, metadata, mode = 'L'):
    out = clean(output)
    out = np.squeeze(out)
    img_ym = Image.fromarray(np.uint8(out), mode)
    path = os.path.join(directory, output_file + ".png")
    img_ym.save(path, pnginfo = to_png_info(metadata))
    return path

"""
    function that reshapes the input to be converted.
    precondition : 
        the input is a list of ndarrays that have the same shape : 2, 3 or 4 dimensions
    param :
        input : list
    return :
        ndarray (reshaped input)
        Shape
"""
def reshape_input(input:list) -> Tuple[np.ndarray,Shape]:    
    if any(input[0].shape != x.shape for x in input):
        raise IncorrectInputDim(f"All arrays must have the same dimensions {[x.shape for x in input]}")
    size = len (np.shape(input[0]))    
    level, time = 1, 1
    if size < 2 :
        raise IncorrectNumberOfVariables(f"{size} < 2 : there are too few variables")
    latitude = input[0].shape[-2]
    longitude = input[0].shape[-1]  
    if size == 4:
        level = input[0].shape[0]
        time = input[0].shape[1]
    elif size == 3 :
        time = input[0].shape[0]
    elif size > 4 :
        raise IncorrectNumberOfVariables(f"{size} > 4 : there are too many variables")
    input_reshaped = np.reshape(input, (len(input), level, time, latitude, longitude))
    return input_reshaped, Shape(level, time, latitude, longitude)

"""
    function that checks the input size and returns the mode.
    precondition :
        the input is a list of maximum 4 ndarrays.
    param :
        size : int (the size of the input)
    return :
        Mode (the mode used to convert as an image)
"""
def get_mode(input : list) -> Mode:
    if len(input) == 0 :
        raise IncorrectInputSize(f"this input list is empty")
    if any(not isinstance(x, np.ndarray) for x in input):
        raise IncorrectInputTypes("at least one input is not ndarray")
    if len(input)==1 :
        mode = Mode.L
    elif len(input) == 2 or len(input) == 3:
        mode = Mode.RGB
    elif len(input) == 4 :
        mode = Mode.RGBA
    else:
        raise IncorrectInputSize(f"{len(input)} > 4 : there are too many inputs")
    return mode

"""
    function that calculates the norm
    param :
        input : ndarray
        _min : float
        _max : float
    return :
        ndarray
"""
def norm(input:np.ndarray, _min:float, _max:float):
    if _min == _max :
        return input 
    return (input - _min)/(_max - _min)

"""
    function that fill the output with normalized input.
    it iterates over levels and times.
    param :
        shape : Shape
        num_var : int
        input : list
        output : np.ndarray
        output_mean : np.ndarray
        threshold : float
        logger : Logger
    return :
        ndarray (the output for one variable)
        List[Dict[str, str]] (the min and max values to be added in the metadata)
        ndarray (the mean over time of the output)
"""
def fill_output(shape:Shape, num_var:int, input:list, output:np.ndarray, output_mean : np.ndarray, threshold : float, logger : Logger) -> Tuple[np.ndarray, List[Dict[str,str]], np.ndarray]:
    min_max = np.empty(shape = (shape.level, shape.time), dtype = dict)
    for index_level in range(shape.level):
        input_mean_times = []
        for index_time in range(shape.time):
                #when only two variables in input -> zeros for the 3rd channel
                if num_var == 2 and len(input) == 2 :
                      input_data = np.zeros((shape.lat, shape.lon))
                else :
                    _min, _max = minmax(input[num_var, index_level, index_time, :, :],threshold, logger)
                    min_max[index_level, index_time] = {"min" : str(_min), "max" : str(_max)}
                    input_data = norm(input[num_var, index_level, index_time, :, :],_min,_max) * 254                
                input_mean_times.append(input_data)
                output[index_level * shape.lat : (index_level+1) * shape.lat,\
                    index_time * shape.lon  : ((index_time+1)* shape.lon),\
                    num_var] = input_data
        #calculates mean over time
        output_mean[index_level * shape.lat : (index_level+1) * shape.lat, :, num_var]\
            = np.nanmean(np.asarray(input_mean_times), axis = 0)
    return output, min_max, output_mean

"""
    calcul of the min and max values.
    param :
        arr : ndarray (some input data)
        threshold : float
        logger : Logger
    return :
        tuple (contains the min and max values)
"""
def minmax(arr : np.ndarray, threshold : float, logger : Logger) -> Tuple[float, float]:
    sorted_flat = np.unique(np.sort(arr.flatten()))
    if np.isnan(sorted_flat[-1]) :
        sorted_flat = sorted_flat[:-1]
    n = len(sorted_flat)
    if n<=1 :
        logger.warning("min and max are equals to 0")
        return 0, 0
    return sorted_flat[int((1-threshold)*n)],sorted_flat[int(threshold*n)]


"""
    main function that sets up the needed variables and checks the input. 
    it iterates over the number of inputs and the number of variables.
    param :
        inputs : List[Tuple[List[Tuple[np.ndarray,VariableSpecificMetadata]],str]]
        threshold : float
        metadata : Metadata
        logger : Logger
        directory : str
    return :
        List[str] (the list of filenames of the created images)
"""
def convert(inputs:List[Tuple[List[Tuple[np.ndarray,VariableSpecificMetadata]],str]], threshold : float, metadata:Metadata, logger : Logger, directory:str = "") -> List[str]:
    png_outputs = []
    for input,output_filename in inputs:
        
        tmp = list(zip(*input))
        input = list(tmp[0])
        vs_metadatas = list(tmp[1])
        
        mode = get_mode(input)
        input, shape = reshape_input(input)    
        output = np.zeros(( shape.lat * shape.level, shape.lon * shape.time, mode.value))
        output_mean = np.zeros ((shape.lat * shape.level, shape.lon, mode.value))
        
        for num_var in range(len(input)) :
            output, min_max, output_mean = fill_output(
                shape,\
                num_var,\
                input,\
                output,\
                output_mean,\
                threshold,\
                logger)
            
            vs_metadatas[num_var].extends(
                min_max = min_max.tolist()
            )
        logger.info(mode.name, "MODE")
        
        metadata.extends(nan_value_encoding = 255,\
            created_at = datetime.now().strftime("%d/%m/%Y_%H:%M:%S"),\
        )
        
        metadata.push(vs_metadatas)
        save(output_mean, output_filename + ".avg", directory, metadata, mode.name)
        filename = save(output, output_filename + ".ts", directory, metadata, mode.name)
        png_outputs.append(filename)
    return png_outputs
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)
    