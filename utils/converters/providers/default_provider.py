from dataclasses import dataclass
from typing import List

import numpy as np
from utils.converters.utils.channel import Channel
from utils.converters.utils.utils import Extension, Mode, Shape
from utils.metadata.metadata import Metadata
import os.path as path
from PIL import Image as img


@dataclass  
class ImageProvider:
    mode : Mode
    extension : Extension
    encoding : type
    lossless : bool
    
    @staticmethod
    def reduce(channels : List[Channel],mode:Mode,encoding:type) -> np.ndarray:
        shape : Shape = channels[0].shape
        
        image = np.zeros((shape.vertical * shape.latitude,
                          shape.time * shape.longitude , 
                          mode.value))
        
        latitude,longitude = shape.latitude,shape.longitude
        for vertical in range(shape.vertical):
            for time in range(shape.time):
                for index,channel in enumerate(channels):
                    image[vertical*latitude:(vertical+1)*latitude ,
                        time*longitude:(time+1)*longitude , index ] = channel.data[vertical,time,:,:]
        return encoding(np.squeeze(image))
    
    def save(self,filename:str,channels : List[Channel],metadata:Metadata) -> str:
        image:np.ndarray = ImageProvider.reduce(channels,self.mode,self.encoding)
        
        file_path = path.join(f"{filename}.{self.extension.value}")
        
        image : img.Image = img.fromarray(image, self.mode.name)
        image.save(file_path , format=self.extension.value,lossless = self.lossless,optimize=True)
        return file_path
    @staticmethod  
    def build(mode : Mode,extension: Extension, lossless:bool) -> 'ImageProvider':
        if mode == Mode.RGBA:
            raise Exception("can't use RGBA by default, only png is supported")
        return ImageProvider(
            encoding=np.int8,
            extension=extension,
            mode=mode,
            lossless = lossless
        )