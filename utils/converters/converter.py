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
    chunks_t : int
    chunks_v : int
    filename : str
    
    def exec(self) -> Tuple[List[str],List[str]]:
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
        
        mean_files = []
        for channels,suffixe in self.slices_vertical(mean_channels):
            mean_files.append(self.provider.save(filename = f"{self.filename}.avg{suffixe}",
                                        channels = mean_channels,
                                   metadata = self.metadata))
        
        return ts_files,mean_files

    def slices(self, converted_channels : List[Channel]):
        sliced_channels = [ch.slices(self.chunks_t, self.chunks_v) for ch in converted_channels]
        n = len(sliced_channels[0])
        for i in range(n):
            channels = [sch[i][0] for sch in sliced_channels]
            yield channels,sliced_channels[0][i][1]
            
    def slices_vertical(self, converted_channels : List[Channel]):
        sliced_channels = [ch.slices(0, self.chunks_v) for ch in converted_channels]
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
        if len(inputs) == 0 :
            raise ChannelDimensionException("No inputs")
            
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
            chunks_t : Union[int , float] , 
            chunks_v : Union[int , float],
            metadata : Metadata,
            lossless : bool) -> 'Converter':
        
        channels , shape = Converter.resolve_channels(inputs=inputs)
        
        if extension == Extension.PNG :
            provider = PNG_Provider.build(mode=Mode.get(channels), lossless = lossless)
        elif extension == Extension.WEBP :
            provider = WEBP_Provider.build(mode=Mode.get(channels), lossless = lossless)
        else :
            provider = ImageProvider.build(mode=Mode.get(channels),extension=extension, lossless = lossless)
        if type(chunks_t) is float:
            chunks_t = int(shape.time/np.ceil(shape.time*chunks_t))
        if type(chunks_v) is float:
            chunks_v = int(shape.vertical/np.ceil(shape.vertical*chunks_v))

        return Converter(channels = channels,
                         shape = shape,
                         nan_encoding = nan_encoding,
                         threshold = threshold,
                         filename = filename,
                         chunks_t = chunks_t,
                         chunks_v = chunks_v,
                         metadata = metadata,
                         provider = provider)
    
    @staticmethod
    def build_all(inputs:List[Tuple[List[Tuple[np.ndarray,VariableSpecificMetadata]],str]],
            metadata:Metadata,
            nan_encoding : int,
            extension : Extension,
            threshold : float,
            chunks_t : Union[int , float],
            chunks_v : Union[int , float],
            lossless : bool) -> List['Converter']:
            
        for input,output_filename in inputs:  
            yield Converter.build(inputs=input,
                                  chunks_t=chunks_t, 
                                  chunks_v =chunks_v,
                                  extension=extension,
                                  filename=output_filename,
                                  metadata=metadata,
                                  nan_encoding=nan_encoding,
                                  threshold=threshold,
                                  lossless = lossless
                                  )