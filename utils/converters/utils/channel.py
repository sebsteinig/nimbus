

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from utils.converters.utils.utils import Shape, bounds, clean, normalize

from utils.metadata.metadata import VariableSpecificMetadata


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
    
    def slices_one_dimension(self,chunks: int, axis : int, data):
            mode = "t" if axis == 1 else "v"
            return [(Channel(
                    metadata=self.metadata,
                    data = slice,
                    shape = Shape(
                        time = slice.shape[1] if axis == 1 else self.shape.time,
                        vertical = slice.shape[0] if axis == 0 else self.shape.vertical,
                        latitude=self.shape.latitude,
                        longitude=self.shape.longitude)),
                    f".{mode}{i+1}of{chunks}") 
                for i,slice in enumerate(data)]

    def slices(self,chunks_t : int, chunks_v : int) -> List['Channel'] :
        if chunks_t <= 0 or chunks_t > self.shape.time:
            if chunks_v <= 0 or chunks_v > self.shape.vertical:
                return [(self,"")]
            else : 
                sliced_arrays = np.array_split(self.data , chunks_v, axis = 0)
                return self.slices_one_dimension(chunks=chunks_v, axis=0, data=sliced_arrays)
        else :
            sliced_arrays = np.array_split(self.data , chunks_t, axis = 1)
            if chunks_v<= 0 or chunks_v > self.shape.vertical:
                return self.slices_one_dimension(chunks=chunks_t, axis = 1, data = sliced_arrays)
            else:
                slices = []
                for slice in sliced_arrays:
                    slices.extend(np.array_split(slice, chunks_v, axis = 0))
                res = []
                for i in range (chunks_t):
                    for j in range(chunks_v):
                        slice = slices[i*chunks_t +j]
                        res.append((Channel(
                        metadata=self.metadata,
                        data = slice,
                        shape = Shape(
                            time = slice.shape[1],
                            vertical = slice.shape[0],
                            latitude=self.shape.latitude,
                            longitude=self.shape.longitude)),
                    f".t{i+1}of{chunks_t}.v{j+1}of{chunks_v}"))
                return res



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
