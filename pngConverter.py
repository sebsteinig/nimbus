import numpy as np
from netCDF4 import Dataset
from PIL import Image
from typing import Tuple
import random


class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass

def save(output : np.ndarray, output_file : str, mode = 'L'):
    out = np.squeeze(output)
    #print(np.uint8(out))
    img_ym = Image.fromarray(np.uint8(out), mode)
    img_ym.save(output_file + ".png")

def eval_shape(input:np.ndarray) -> tuple[bool, bool, dict]:
    res = {}
    levelExists = False
    match len (np.shape(input[0])):
        case 4:
            res["level"] = input[0].shape[0]
            res["time"] = input[0].shape[1]
            levelExists = True
            timeExists = True
        case 3 :
            res["time"] = input[0].shape[0]
            timeExists = True
        case 2:
            timeExists = False
        case _ :
            raise TooManyVariables(f"{len (np.shape(input[0]))} > 4 : there are too many variables")
    res["latitude"] = input[0].shape[-2]
    res["longitude"] = input[0].shape[-1]  
    return timeExists, levelExists, res

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
            
def shape_output(shapes:dict, timeExists:bool, levelExists:bool, dim:int) -> np.ndarray :
    if timeExists :
        output = np.zeros( ( shapes["latitude"] * shapes["level"], shapes["longitude"] * shapes["time"], dim) )\
            if levelExists else np.zeros( ( shapes["latitude"], shapes["longitude"] * shapes["time"], dim) )
    else :        
        output = np.zeros( ( shapes["latitude"] * shapes["level"], shapes["longitude"], dim) )\
            if levelExists else np.zeros( ( shapes["latitude"], shapes["longitude"], dim) )
    return output
        


def convert_with_time(time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for index in range(time):
            if(len(input) == 1) :
                output[:,index* longitude  : ((index+1)* longitude), 0] = \
                norm(input[0][index,:,:]) * 255
            elif numVar == 2 and len(input) == 2:
                output[:,index* longitude  : ((index+1)* longitude), numVar ] = \
                    np.zeros((latitude, longitude))
            else :
                output[:,index* longitude : ((index+1)* longitude), numVar ] = \
                norm(input[numVar][index,:,:]) * 255 
    return output

def convert_with_time_and_level(level:int, time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for lev in range(level):
        for index in range(time):
            if(len(input) == 1) :
                output[lev*latitude : (lev+1)*latitude, index* longitude  : ((index+1)* longitude), 0] = \
                    norm(input[0][lev,index,:,:]) * 255
            elif numVar == 2 and len(input) == 2:
                output[lev*latitude : (lev+1)*latitude,index* longitude  : ((index+1)* longitude), numVar ] = \
                    np.zeros((latitude, longitude))
            else :
                output[lev*latitude : (lev+1)*latitude,index* longitude : ((index+1)* longitude), numVar ] = \
                    norm(input[numVar][lev, index,:,:]) * 255 
    return output

def convert_with_level(level:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for lev in range(level):
            if(len(input) == 1) :
                output[lev*latitude : (lev+1)*latitude, :, 0] = \
                norm(input[0][lev,:,:]) * 255
            elif numVar == 2 and len(input) == 2:
                output[lev*latitude : (lev+1)*latitude,:, numVar] = \
                    np.zeros((latitude, longitude))
            else :
                output[lev*latitude : (lev+1)*latitude,:, numVar] = \
                norm(input[numVar][lev,:,:]) * 255 
    return output

def norm(input:np.ndarray):
    _min = input.min()
    _max = input.max()
    return (input - _min)/(_max - _min)

def convert_with_space_only (longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:

    if(len(input) == 1) :
        output[:,:, 0]= norm(input[0]) * 255
    elif numVar == 2 and len(input) == 2:
        output[:,:, numVar] = np.zeros((latitude, longitude))
    else :
        output[:,:, numVar] = norm(input[numVar]) * 255 
    return output

def convert(input:list, output_filename:str) -> str:
    dim, mode = eval_input(len(input))
    timeExists, levelExists, shapes = eval_shape(input)
    output = shape_output(shapes, timeExists, levelExists, dim)
    for numVar in range(dim) :
        if timeExists:
            if levelExists :
                output = convert_with_time_and_level(shapes["level"], shapes["time"], shapes["longitude"], shapes["latitude"], numVar, input, output)
            else :
                output = convert_with_time(shapes["time"], shapes["longitude"], shapes["latitude"], numVar, input, output)
        else:
            if levelExists:
                output = convert_with_level(shapes["level"], shapes["longitude"], shapes["latitude"], numVar, input, output)
            else:
                output = convert_with_space_only(shapes["longitude"], shapes["latitude"], numVar, input, output)
    save(output, output_filename, mode)
    return output_filename

    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)