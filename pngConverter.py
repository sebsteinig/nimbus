import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import os

class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass
class LongitudeLatitude(Exception):pass

def clean(output : np.ndarray) -> np.ndarray:
    output[np.isnan(output)] = 0
    return output.clip(0,254)

def assert_input(data):
    if all(x<y for x, y in zip(data, data[1:])):
        data = np.flip(data,0)

def assert_long_lat(data, limit):
    if min(data) < (- limit) or max(data) > limit:
        raise LongitudeLatitude(f"{min(data)} or {max(data)} exceeded the limit {limit}")

def save(output : np.ndarray, output_file : str, directory :str, metadata : list, mode = 'L'):
    out = clean(output)
    out = np.squeeze(out)
    img_ym = Image.fromarray(np.uint8(out), mode)
    path = os.path.join(directory, output_file + ".png")
    img_ym.save(path, pnginfo = metadata)
    return path

def eval_shape(input:list) -> tuple[bool, bool, dict]:
    level, time = 1, 1
    latitude = input[0].shape[-2]
    longitude = input[0].shape[-1]  
    size = len (np.shape(input[0]))    
    match size:
        case 4:
            level = input[0].shape[0]
            time = input[0].shape[1]
        case 3 :
            time = input[0].shape[0]
        case _ :
            if not(size == 2) :
                raise TooManyVariables(f"{size} > 4 : there are too many variables")
    #print(type(input))
    input_reshaped = np.reshape(input, (len(input), level, time, latitude, longitude))
    #print(input_reshaped.shape)
    return input_reshaped, level, time, latitude, longitude

def eval_input(size:int) -> tuple[int, str]:
    match size:
        case 1 :
            dim = 1
            mode = 'L'
        case 2|3:
            dim = 3
            mode = 'RGB'
        case 4 :
            dim = 4
            mode = "RGBA"
        case _:
            raise TooManyInputs(f"{size} > 4 : there are too many inputs")
    return dim, mode
         
def initMetadata(latitude, longitude):
    metadata = PngInfo()
    metadata.add_text("latitude", str(latitude))
    metadata.add_text("longitude", str(longitude))
    return metadata

def norm(input:np.ndarray,_min,_max):
    return (input - _min)/(_max - _min)

def get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude):
    if level == 1 :
        index_output = np.s_[:,:,numVar] if  time == 1 else\
             np.s_[:, indexTime * longitude  : ((indexTime+1)* longitude), numVar]
    else :
        index_output = np.s_[indexLevel *latitude : (indexLevel+1)*latitude, indexTime* longitude  : ((indexTime+1)* longitude), numVar]
    return index_output

def fill_output(level:int, time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray,_min,_max) -> np.ndarray:
    for indexLevel in range(level):
        for indexTime in range(time):
                if numVar ==2 and len(input) == 2 :
                      input_data = np.zeros((latitude, longitude))
                else :
                    input_data = norm(input[numVar, indexLevel, indexTime, :, :],_min,_max) * 255
                index_output = get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude)
                output[index_output] = input_data
    return output

def minmax(arr,threshold):
    sorted_flat = np.unique(np.sort(arr.flatten()))
    n = len(sorted_flat)
    return sorted_flat[int((1-threshold)*n)],sorted_flat[int(threshold*n)]

def convert(input:list, output_filename:str, directory:str = "") -> str:
    dim, mode = eval_input(len(input))
    input, level, time, latitude, longitude = eval_shape(input)
    metadata = initMetadata(latitude, longitude)
    output = np.zeros(( latitude * level, longitude * time, dim))
    threshold = 0.90
    for numVar in range(len(input)) :
        _min, _max = minmax(input[numVar],threshold)
        output = fill_output(level, time, longitude, latitude, numVar, input, output,_min,_max)
        metadata.add_text(f"min{numVar}", str(_min))
        metadata.add_text(f"max{numVar}", str(_max))
    filename = save(output, output_filename, directory, metadata, mode)
    print(f"\tsave : {filename}")
    return filename
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)
    