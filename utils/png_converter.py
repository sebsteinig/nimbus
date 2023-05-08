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
from typing import List, Tuple

class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass
class LongitudeLatitude(Exception):pass

@dataclass
class Shape:
    level:int
    time:int
    lat:int
    lon:int


def clean(output : np.ndarray) -> np.ndarray:
    output[np.isnan(output)] = 255
    return output.clip(0,254)

def to_png_info(metadata):
    png_info = PngInfo()
    for key,value in metadata.to_dict().items():
        png_info.add_text(key,str(json.dumps(value)))
    return png_info

def save(output : np.ndarray, output_file : str, directory :str, metadata, mode = 'L'):
    out = clean(output)
    out = np.squeeze(out)
    img_ym = Image.fromarray(np.uint8(out), mode)
    path = os.path.join(directory, output_file + ".png")
    img_ym.save(path, pnginfo = to_png_info(metadata))
    return path

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

def norm(input:np.ndarray,_min,_max):
    if _min == _max :
        return input 
    return (input - _min)/(_max - _min)

def get_index_output(num_var, index_level, index_time,shape:Shape) :
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

def fill_output(shape:Shape, num_var:int, input:list, output:np.ndarray, output_mean, threshold, logger) -> np.ndarray:
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
        Logger.console().debug(f"output image dynamic range for last timestep: min={float(minmaxTimes[-1]['min']):.2f}, max={float(minmaxTimes[-1]['max']):.2f}")
        output_mean[get_index_output(num_var, index_level, 0, shape)] = np.nanmean(np.asarray(input_mean_times),  axis = 0)
        i = get_index_output(num_var, index_level, 0, shape)
        #output_mean[i] = np.mean(np.asarray(input_mean_times), dtype='int', axis = 0)
    return output, min_max, output_mean

def minmax(arr,threshold, logger):
    # filter outliers from 1D array without NaN values
    arr_clean = reject_outliers(arr.flatten()[~np.isnan(arr.flatten())], threshold)
    return np.min(arr_clean),np.max(arr_clean)

def reject_outliers(data, m = 3.):
    # https://stackoverflow.com/a/16562028
    # remove outliers based on distribution of the data
    # median is more robust than the mean to outliers and the standard
    # deviation is replaced with the median absolute distance to the median
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else np.zeros(len(d))
    return data[s<m]

def convert(inputs:List[Tuple[List[Tuple[np.ndarray,VariableSpecificMetadata]],str]], threshold, metadata:Metadata, logger, directory:str = "") -> List[str]:
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
    