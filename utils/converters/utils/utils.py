from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
import numpy as np

class NumberOfChannelException(Exception) : pass
class ChannelDimensionException(Exception) : pass

"""
    function that calculates the norm
    param :
        input : ndarray
        _min : float
        _max : float
    return :
        ndarray
"""
def normalize(input:np.ndarray, min:float, max:float):
    if min == max :
        return input 
    return (input - min)/(max - min)

"""
    function that replaces nan values with 255 in the output.
    param :
        output : ndarray
    return :
        ndarray
"""
def clean(output : np.ndarray, nan_encoding:int) -> np.ndarray:
    output[np.isnan(output)] = nan_encoding
    if nan_encoding == 0:
        return output.clip(1,255)
    else :
        return output.clip(0,254)
    
"""
    calcul of the min and max values.
    param :
        arr : ndarray (some input data)
        threshold : float
        logger : Logger
    return :
        tuple (contains the min and max values)
"""   
def bounds(arr : np.ndarray, threshold : float) -> Tuple[float, float]:
    # filter outliers from 1D array without NaN values
    arr_clean = reject_outliers(arr.flatten()[~np.isnan(arr.flatten())], threshold)
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
def reject_outliers(data, m = 3.):
    d = np.abs(data - np.ma.median(data))
    mdev = np.ma.median(d)
    s = d/mdev if mdev else np.zeros(len(d))
    return data[s<m]

"""
    enum Mode for creating an image, with the number of channels as value
"""
class Mode(Enum):
    L = 1
    RGB = 3
    RGBA = 4
    @staticmethod
    def get(channels : list) -> 'Mode':
        n = len(channels)
        if n == 2 or n == 3:
            return Mode.RGB
        if n == 1 :
            return Mode.L
        if n == 4 : 
            return Mode.RGBA
        raise NumberOfChannelException(f"Incorrect number of channels : {n} must be between 1 and 4")
         
         
class Extension(Enum):
    PNG = 'png'
    WEBP = 'webp'
    BMP = 'bmp'
    JPEG = 'jpeg'
    TGA = 'tga'
    
    
@dataclass
class Shape:
    time : int
    vertical : int
    latitude : int
    longitude : int
    
    def tuple(self) -> Tuple[int,int,int,int]:
        return (self.vertical,self.time,self.latitude,self.longitude)
    
    @staticmethod
    def build(shape:List[int]) -> 'Shape':
        latitude = shape[-2]
        longitude = shape[-1]  
        vertical = 1
        time = 1
        if len(shape) == 4:
            vertical = shape[0]
            time = shape[1]
        elif len(shape) == 3 :
            time = shape[0]
        return Shape(time=time,vertical=vertical,latitude=latitude,longitude=longitude)
    