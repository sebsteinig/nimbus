import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import os
import json
from datetime import datetime
from utils.metadata import Metadata
from utils.logger import Logger,_Logger
from typing import Tuple

class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass
class LongitudeLatitude(Exception):pass

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

def eval_shape(input:list) -> Tuple[bool, bool, dict]:
    level, time = 1, 1
    latitude = input[0].shape[-2]
    longitude = input[0].shape[-1]  
    size = len (np.shape(input[0]))    
    if size == 4:
        level = input[0].shape[0]
        time = input[0].shape[1]
    elif size == 3 :
        time = input[0].shape[0]
    else:
        if not(size == 2) :
            raise TooManyVariables(f"{size} > 4 : there are too many variables")
    input_reshaped = np.reshape(input, (len(input), level, time, latitude, longitude))
    return input_reshaped, level, time, latitude, longitude

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

def get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude):
    if level == 1 :
        index_output = np.s_[:,:,numVar] if  time == 1 else\
             np.s_[:, indexTime * longitude  : ((indexTime+1)* longitude), numVar]
    else :
        index_output = np.s_[indexLevel *latitude : (indexLevel+1)*latitude, indexTime* longitude  : ((indexTime+1)* longitude), numVar]
    return index_output

def fill_output(level:int, time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray, threshold, logger) -> np.ndarray:
    minmaxTab = []
    for indexLevel in range(level):
        minmaxTimes = []
        for indexTime in range(time):
                if numVar ==2 and len(input) == 2 :
                      input_data = np.zeros((latitude, longitude))
                else :
                    _min, _max = minmax(input[numVar, indexLevel, indexTime, :, :],threshold, logger)
                    minmaxTimes.append({"min" : str(_min), "max" : str(_max)})
                    input_data = norm(input[numVar, indexLevel, indexTime, :, :],_min,_max) * 254
                index_output = get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude)
                output[index_output] = input_data
        minmaxTab.append(minmaxTimes)
    return output, minmaxTab

def minmax(arr,threshold, logger):
    sorted_flat = np.unique(np.sort(arr.flatten()))
    if np.isnan(sorted_flat[-1]) :
        sorted_flat = sorted_flat[:-1]
    n = len(sorted_flat)
    if n<=1 :
        logger.warning("min and max are equals to 0")
        return 0, 0
    return sorted_flat[int((1-threshold)*n)],sorted_flat[int(threshold*n)]



def convert(input:list, output_filename:str, threshold, metadata:Metadata, logger, directory:str = "") -> str:
    dim, mode = eval_input(len(input))
    input, level, time, latitude, longitude = eval_shape(input)    
    output = np.zeros(( latitude * level, longitude * time, dim))
    minmaxVars = []
    for numVar in range(len(input)) :
        output, minmaxTab = fill_output(level, time, longitude, latitude, numVar, input, output, threshold, logger)
        minmaxVars.append(minmaxTab)
    logger.info(mode, "MODE")
    
    metadata.extends(nan_value_encoding = 255,\
        created_at = datetime.now().strftime("%d/%m/%Y_%H:%M:%S"),\
        min_max = str(json.dumps(minmaxVars))
    )
    
    filename = save(output, output_filename, directory, metadata, mode)
    print(f"\tsave : {filename}")
    return filename
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)
    