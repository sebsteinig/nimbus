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

class IncorrectInputTypes(Exception): pass
class IncorrectInputDim(Exception) : pass
class IncorrectNumberOfVariables(Exception) : pass
class IncorrectInputSize(Exception) : pass

"""
    enum Mode for creating an image, with the number of channels as value
"""
class Mode(Enum):
    L = 1
    RGB = 3
    RGBA = 4

"""
    class PngConverter, which contains 4 non static methods which are called by the convert function.
"""
class PngConverter :
    level:int
    time:int
    lat:int
    lon:int
    mode : Mode
    input : list
    output : np.ndarray
    output_mean : np.ndarray

    """
        (1/4) constructor of the PngConverter. intializes the size of the outputs
        param :
            input : a list of ndarrays
        return :
            None
    """
    def __init__(self, input):
        self.mode = PngConverter.get_mode(input)
        self.input, self.level, self.time, self.lat, self.lon = PngConverter.reshape_input(input)
        self.output = np.zeros(( self.lat * self.level, self.lon * self.time, self.mode.value))
        self.output_mean = np.zeros ((self.lat * self.level, self.lon, self.mode.value))

    """
        (2/4) calculates the output
        param :
            vs_metadatas : list
            metadata : Metadata
            threshold : float
            logger : Logger
        return :
            Metadata
    """
    def set_output(self, vs_metadatas : list, metadata : Metadata, threshold : float, logger : Logger) -> Metadata:
        for num_var in range(len(self.input)) :
            min_max = self.fill_output(num_var, threshold, logger)
            vs_metadatas[num_var].extends( min_max = min_max.tolist() )
        logger.info(self.mode.name, "MODE")        
        metadata.extends( nan_value_encoding = 255, created_at = datetime.now().strftime("%d/%m/%Y_%H:%M:%S") )
        metadata.push(vs_metadatas)
        return metadata

    """
        (3/4) save the output as a png image, and calculates the mean
        param :
            directory : str
            output_filename:str
            png_outputs : list
            metadata : Metadata
        return :
            list (the name of the newly created file is added to te list)
    """
    def save_output(self, directory : str, output_filename:str, png_outputs : list, metadata : Metadata) -> list:    
        out = PngConverter.clean(self.output)
        ### calcul of output_mean, after cleaning the output ###
        for num_var in range (self.mode.value):
            for index_level in range(self.level):
                arr = np.reshape(out[index_level * self.lat : (index_level+1) * self.lat, :, num_var], (self.lat, self.time, self.lon))
                self.output_mean[index_level * self.lat : (index_level+1) * self.lat, :, num_var] = np.mean(arr, axis = 1)
        ### save two png files : "avg" for the output_mean and "ts" for the cleaned output ###
        PngConverter.save(self.output_mean, output_filename + ".avg", directory, metadata, self.mode.name)
        filename = PngConverter.save(out, output_filename + ".ts", directory, metadata, self.mode.name)
        png_outputs.append(filename)
        return png_outputs

    """
        (4/4) function that fill the output with normalized input.
        it iterates over levels and times.
        param :
            num_var : int
            threshold : float
            logger : Logger
        return :
            ndarray (of size (level x time) where each element is a dict containing min and max values)
    """
    def fill_output(self, num_var:int, threshold : float, logger : Logger) -> np.ndarray :
        min_max = np.empty(shape = (self.level, self.time), dtype = dict)
        for index_level in range(self.level):
            for index_time in range(self.time):
                    ### when only two variables in input -> zeros for the 3rd channel ###
                    if num_var == 2 and len(self.input) == 2 :
                        input_data = np.zeros((self.lat, self.lon))
                    else :
                        _min, _max = PngConverter.minmax(self.input[num_var, index_level, index_time, :, :], threshold, logger)
                        ### min and max values that will be added to the metadata ###
                        min_max[index_level, index_time] = {"min" : str(_min), "max" : str(_max)}
                        input_data = PngConverter.norm(self.input[num_var, index_level, index_time, :, :],_min,_max) * 254 
                    self.output[index_level * self.lat : (index_level+1) * self.lat,\
                        index_time * self.lon  : ((index_time+1)* self.lon), num_var] = input_data
        return min_max
  

    """
        function that reshapes the input to be converted.
        precondition : 
            the input is a list of ndarrays that have the same shape : 2, 3 or 4 dimensions
        param :
            input : list
        return :
            (ndarray, int, int, int, int, int) (reshaped input and the 4 dimensions)
    """
    @staticmethod
    def reshape_input(input:list) -> Tuple[np.ndarray, int, int, int, int]:    
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
        return input_reshaped, level, time, latitude, longitude

    """
        function that checks the input size and returns the mode.
        precondition :
            the input is a list of maximum 4 ndarrays.
        param :
            input : list
        return :
            Mode (the mode used to convert as an image)
    """
    @staticmethod
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
        calcul of the min and max values.
        param :
            arr : ndarray (some input data)
            threshold : float
            logger : Logger
        return :
            tuple (contains the min and max values)
    """
    @staticmethod
    def minmax(arr : np.ndarray, threshold : float, logger : Logger) -> Tuple[float, float]:
        # filter outliers from 1D array without NaN values
        arr_clean = PngConverter.reject_outliers(arr.flatten()[~np.isnan(arr.flatten())], threshold)
        if len(arr_clean) == 0:
            return 0, 0
        return np.min(arr_clean),np.max(arr_clean)

    """
        remove outliers based on distribution of the data
        median is more robust than the mean to outliers and the standard
        deviation is replaced with the median absolute distance to the median
        https://stackoverflow.com/a/16562028
        param :
            data : ndarray
            m : float
        return :
            ndarray
    """
    @staticmethod
    def reject_outliers(data, m = 3.):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d/mdev if mdev else np.zeros(len(d))
        return data[s<m]
    
    """
        function that calculates the norm
        param :
            input : ndarray
            _min : float
            _max : float
        return :
            ndarray
    """
    @staticmethod
    def norm(input:np.ndarray, _min:float, _max:float):
        if _min == _max :
            return input 
        return (input - _min)/(_max - _min)
 
    """
        function that replaces nan values with 255 in the output.
        param :
            output : ndarray
        return :
            ndarray
    """
    @staticmethod
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
    @staticmethod
    def to_png_info(metadata : Metadata) -> PngInfo:
        png_info = PngInfo()
        for key,value in metadata.to_dict().items():
            png_info.add_text(key,str(json.dumps(value)))
        return png_info
          
    """
        save the png image
        param :
            out : ndarray
            output_file : str (name of the image file)
            directory : str (name of the ouput directory)
            metadata : PngInfo
            mode : str (L or RGB or RGBA)
        return :
            str (the path to the output image)
    """
    @staticmethod
    def save(out : np.ndarray, output_file : str, directory :str, metadata : Metadata, mode = 'L'):        
        img_ym = Image.fromarray(np.uint8(np.squeeze(out)), mode)
        path = os.path.join(directory, output_file + ".png")
        img_ym.save(path, pnginfo = PngConverter.to_png_info(metadata))
        return path


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
        png_converter = PngConverter(input)         
        metadata = png_converter.set_output(vs_metadatas, metadata, threshold, logger)
        png_outputs = png_converter.save_output(directory, output_filename, png_outputs, metadata)
    return png_outputs
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)
    