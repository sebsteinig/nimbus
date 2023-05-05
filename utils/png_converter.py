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

class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass
class LongitudeLatitude(Exception):pass

@dataclass
class Shape:
    level:int
    time:int
    lat:int
    lon:int

"""
    functions that replace nan values with 255.
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
    functions that reshape the input to be converted.
    precondition : 
        the input is a list of ndarrays that have the same shape : 2, 3 or 4 dimensions
    param :
        input : list
    return :
        ndarray (reshaped input)
        Shape
"""
def eval_shape(input:list) -> Tuple[np.ndarray,Shape]:    
    if any(input[0].shape != x.shape for x in input):
        raise Exception(f"All arrays must have the same dimensions {[x.shape for x in input]}")
    level, time = 1, 1
    latitude = input[0].shape[-2]
    longitude = input[0].shape[-1]  
    size = len (np.shape(input[0]))    
    if size == 4:
        level = input[0].shape[0]
        time = input[0].shape[1]
    elif size == 3 :
        time = input[0].shape[0]
    elif size > 4 :
        raise TooManyVariables(f"{size} > 4 : there are too many variables")
    elif size < 2 :
        raise TooManyVariables(f"{size} < 2 : there are too few variables")
    input_reshaped = np.reshape(input, (len(input), level, time, latitude, longitude))
    return input_reshaped, Shape(level, time, latitude, longitude)

"""
    functions that check the input size.
    precondition :
        the input is a list of maximum 4 ndarrays.
    param :
        size : int (the size of the input)
    return :
        int (the number of channels)
        str (the mode used to convert as an image)
"""
def eval_input(size:int) -> Tuple[int, str]:
    if size==1 :
        dim = 1
        mode = 'L'
    elif size == 2 or size == 3:
        dim = 3
        mode = 'RGB'
    elif size == 4 :
        dim = 4
        mode = "RGBA"
    else:
        raise TooManyInputs(f"{size} > 4 : there are too many inputs")
    return dim, mode

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
    get the indexes to fill the output
    param :
        num_var : int
        index_level : int
        index_time : int
        shape : Shape
    return :
        tuple (indexes)
"""
def get_index_output(num_var:int, index_level:int, index_time:int,shape:Shape)-> tuple:
    level, time, latitude, longitude = shape.level,shape.time,shape.lat,shape.lon    
    if level == 1 :
        if  time == 1:
            index_output = np.s_[:,:,num_var] 
        else :
            index_output = np.s_[:, index_time * longitude  : ((index_time+1)* longitude), num_var]
    else :
        index_output = np.s_[
            index_level *latitude : (index_level+1)*latitude,\
            index_time* longitude  : ((index_time+1)* longitude),\
            num_var]
    return index_output

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
    min_max = []
    for index_level in range(shape.level):
        minmaxTimes = []
        input_mean_times = []
        for index_time in range(shape.time):
                if num_var ==2 and len(input) == 2 :
                      input_data = np.zeros((shape.lat, shape.lon))
                else :
                    _min, _max = minmax(input[num_var, index_level, index_time, :, :],threshold, logger)
                    minmaxTimes.append({"min" : str(_min), "max" : str(_max)})
                    input_data = norm(input[num_var, index_level, index_time, :, :],_min,_max) * 254
                index_output = get_index_output(num_var, index_level, index_time, shape)
                output[index_output] = input_data
                input_mean_times.append(input_data)
        min_max.append(minmaxTimes)
        output_mean[get_index_output(num_var, index_level, 0, shape)] = np.nanmean(np.asarray(input_mean_times),  axis = 0)
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
        
        dim, mode = eval_input(len(input))
        input, shape= eval_shape(input)    
        output = np.zeros(( shape.lat * shape.level, shape.lon * shape.time, dim))
        output_mean = np.zeros ((shape.lat * shape.level, shape.lon, dim))
        
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
                min_max = min_max
            )
        logger.info(mode, "MODE")
        
        metadata.extends(nan_value_encoding = 255,\
            created_at = datetime.now().strftime("%d/%m/%Y_%H:%M:%S"),\
        )
        
        metadata.push(vs_metadatas)
        filename_mean = save(output_mean, output_filename + ".avg", directory, metadata, mode)
        filename = save(output, output_filename + ".ts", directory, metadata, mode)
        png_outputs.append(filename)
    return png_outputs
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)
    