

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from utils.converters.utils.utils import Shape, bounds, clean, normalize

from utils.metadata import VariableSpecificMetadata


@dataclass
class Channel:
    metadata : VariableSpecificMetadata
    data : np.ndarray
    shape : Shape
    
    def mean(self) -> 'Channel':
        mean = np.mean(self.data, axis = 1, dtype = int,keepdims=True)
        return Channel(
            metadata = self.metadata,
            data = mean,
            shape = Shape(
                time=1,
                latitude=self.shape.latitude,
                longitude=self.shape.longitude,
                vertical=self.shape.vertical
            )
        )
    def convert(self,nan_encoding:int,threshold:float) -> 'Channel':
        converted_data = np.zeros(self.data.shape)
        bounds_matrix = np.empty(shape = (self.shape.vertical, self.shape.time), dtype = dict)
        
        for vertical in range(self.shape.vertical):
            for time in range(self.shape.time):
                converted_data[vertical,time,:,:],(min,max) = self.__convert_tile(vertical=vertical,
                                                                                  time=time,
                                                                                  threshold=threshold,
                                                                                  nan_encoding=nan_encoding)
                bounds_matrix[vertical,time] = {"min" : str(min), "max" : str(max)}
        
        self.metadata.extends(bounds_matrix = bounds_matrix.tolist())
        converted_data = clean(converted_data,nan_encoding=nan_encoding)
        return Channel(
            metadata = self.metadata,
            data = converted_data,
            shape = self.shape 
        )
        
    def slices(self,chunks : int ) -> List['Channel'] :
        if chunks <= 0 or chunks > self.shape.time :
            return [(self,"")]
        else :
            sliced_arrays = np.array_split(self.data , chunks, axis = 1)
            
            return [       
                (Channel(
                    metadata=self.metadata,
                    data = slice,
                    shape = Shape(
                        time = slice.shape[1],
                        vertical = self.shape.vertical,
                        latitude=self.shape.latitude,
                        longitude=self.shape.longitude
                    )
                ),f".{i+1}of{chunks}") 
                for i,slice in enumerate(sliced_arrays)
            ]
    
    def __convert_tile(self,
                       vertical:int,
                       time:int,
                       nan_encoding:int,
                       threshold:float) -> Tuple[np.ndarray,Tuple[float,float]]:
        
        min,max = bounds(arr=self.data[vertical,time,:,:],threshold=threshold)
        normalized = normalize(input=self.data[vertical,time,:,:],min = min, max = max )
        if nan_encoding == 0 :
            normalized = normalized * 254 + 1
        else :
            normalized = normalized * 254
        return normalized,(min,max)
