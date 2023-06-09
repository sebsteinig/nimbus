from dataclasses import dataclass
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import os
import json
from datetime import datetime
from utils.converters.providers.default_provider import ImageProvider
from utils.converters.providers.png_provider import PNG_Provider
from utils.converters.providers.webp_provider import WEBP_Provider
from utils.converters.utils.channel import Channel
from utils.converters.utils.utils import ChannelDimensionException, Extension, Mode, Shape, bounds, clean, normalize
from utils.metadata.metadata import Metadata,VariableSpecificMetadata
from utils.logger import Logger,_Logger
from typing import List, Tuple, Dict, Union
from enum import Enum


@dataclass
class Converter:
    channels : List[Channel]
    metadata : Metadata
    provider : ImageProvider
    shape : Shape
    nan_encoding : int
    threshold : float
    chunks : Union[int , float]
    filename : str
    
    def exec(self) -> Tuple[List[str],str]:
        converted_channels = self.convert()
        
        mean_channels = self.mean(converted_channels)
        
        self.metadata.extends( nan_value_encoding = self.nan_encoding,
                              created_at = datetime.now().strftime("%d/%m/%Y_%H:%M:%S") )

        self.metadata.push((channel.metadata for channel in converted_channels))
        
        ts_files = []
        for channels,suffixe in self.slices(converted_channels):
            ts_files.append(self.provider.save(filename = f"{self.filename}.ts{suffixe}" ,
                                   channels = channels,
                                   metadata = self.metadata))
            
        mean_file = self.provider.save(filename = self.filename + ".avg",
                                        channels = mean_channels,
                                   metadata = self.metadata)
        
        return ts_files,mean_file

    def slices(self, converted_channels : List[Channel]):
        
        chunks = self.chunks
        if type(chunks) is float:
            chunks = int(self.shape.time/np.ceil(self.shape.time*chunks))
        
        sliced_channels = [ch.slices(chunks) for ch in  converted_channels]
        n = len(sliced_channels[0])
        for i in range(n):
            channels = [sch[i][0] for sch in sliced_channels]
            yield channels,sliced_channels[0][i][1]
            

    def convert(self) -> List[Channel]:
        converted_channels : List[Channel] = []
        for channel in self.channels : 
            converted_channels.append(channel.convert(nan_encoding=self.nan_encoding,
                                                      threshold = self.threshold)) 
        return converted_channels
    
    def mean(self,channels:List[Channel]) -> List[Channel]:
        mean_channels : List[Channel] = []
        for channel in channels : 
            mean_channels.append(channel.mean()) 
        return mean_channels
    
    @staticmethod
    def resolve_channels(inputs : List[Tuple[np.ndarray,VariableSpecificMetadata]]) -> Tuple[List[Channel],Shape]:
        if any(inputs[0][0].shape != data.shape for data,_ in inputs):
            raise ChannelDimensionException("All inputs must have the same shape")
        shape = inputs[0][0].shape
        if len(shape) < 2 :
            raise ChannelDimensionException(f"{len(shape)} < 2 : there are too few dimensions, inputs must contains at least latitude and longitude")
        shape = Shape.build(shape)
        channels = []
        for data,metadata in inputs:
            data = np.reshape(data, shape.tuple())
            channels.append(
                Channel(
                    metadata = metadata,
                    data = data,
                    shape = shape)
                )
        return channels,shape
    
    @staticmethod
    def build(inputs : List[Tuple[np.ndarray,VariableSpecificMetadata]],
            extension : Extension,
            nan_encoding : int,
            threshold : float,
            filename : str,            
            chunks : int,
            metadata : Metadata,
            lossless : bool) -> 'Converter':
        
        channels , shape = Converter.resolve_channels(inputs=inputs)
        
        if extension == Extension.PNG :
            provider = PNG_Provider.build(mode=Mode.get(channels), lossless = lossless)
        elif extension == Extension.WEBP :
            provider = WEBP_Provider.build(mode=Mode.get(channels), lossless = lossless)
        else :
            provider = ImageProvider.build(mode=Mode.get(channels),extension=extension, lossless = lossless)
        
        
        return Converter(channels = channels,
                         shape = shape,
                         nan_encoding = nan_encoding,
                         threshold = threshold,
                         filename = filename,
                         chunks = chunks,
                         metadata = metadata,
                         provider = provider)
    
    @staticmethod
    def build_all(inputs:List[Tuple[List[Tuple[np.ndarray,VariableSpecificMetadata]],str]],
            metadata:Metadata,
            nan_encoding : int,
            extension : Extension,
            threshold : float,
            chunks : int,
            lossless : bool) -> List['Converter']:
            
        for input,output_filename in inputs:  
            yield Converter.build(inputs=input,
                                  chunks=chunks,
                                  extension=extension,
                                  filename=output_filename,
                                  metadata=metadata,
                                  nan_encoding=nan_encoding,
                                  threshold=threshold,
                                  lossless = lossless
                                  )