import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import os

class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass

def clean(output : np.ndarray) -> np.ndarray:
    output[output > 255] = 255
    output[output < 0] = 0
    output[np.isnan(output)] = 0
    return output

def save(output : np.ndarray, output_file : str, directory :str, metadata : list, mode = 'L'):
    out = clean(output)
    out = np.squeeze(out)
    img_ym = Image.fromarray(np.uint8(out), mode)
    path = os.path.join(directory, output_file + ".png")
    img_ym.save(path, pnginfo = metadata)
    return path

def eval_shape(input:np.ndarray) -> tuple[bool, bool, dict]:
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
    input = np.reshape(input, (len(input), level, time, latitude, longitude))
    return input, level, time, latitude, longitude

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

def norm(input:np.ndarray):
    _min = input.min()
    _max = input.max()
    return (input - _min)/(_max - _min)

def get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude):
    if level == 1 :
        index_output = np.s_[:,:,numVar] if  time == 1 else\
             np.s_[:, indexTime * longitude  : ((indexTime+1)* longitude), numVar]
    else :
        index_output = np.s_[indexLevel *latitude : (indexLevel+1)*latitude, indexTime* longitude  : ((indexTime+1)* longitude), numVar]
    return index_output

def fill_output(level:int, time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for indexLevel in range(level):
        for indexTime in range(time):
                if numVar ==2 and len(input) == 2 :
                      input_data = np.zeros((latitude, longitude))
                else :
                    input_data = norm(input[numVar, indexLevel, indexTime, :, :]) * 255
                index_output = get_index_output(numVar, indexLevel, indexTime, level, time, latitude, longitude)
                output[index_output] = input_data
    return output

def convert(input:list, output_filename:str, directory:str = "") -> str:
    dim, mode = eval_input(len(input))
    input, level, time, latitude, longitude = eval_shape(input)
    metadata = initMetadata(latitude, longitude)
    output = np.zeros(( latitude * level, longitude * time, dim))
    for numVar in range(dim) :
        output = fill_output(level, time, longitude, latitude, numVar, input, output)
        metadata.add_text(f"min{numVar}", str(input.min()))
        metadata.add_text(f"max{numVar}", str(input.max()))
    filename = save(output, output_filename, directory, metadata, mode)
    return filename
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)