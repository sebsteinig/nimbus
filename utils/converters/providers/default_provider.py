from dataclasses import dataclass
from typing import List

import numpy as np
from utils.converters.utils.channel import Channel
from utils.converters.utils.utils import Extension, Mode, Shape


@dataclass  
class ImageProvider:
    mode : Mode
    extension : Extension
    encoding : type
    
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
    
    def save(self,filename:str,channels : List[Channel]) -> List[str]:pass
    
    @staticmethod  
    def build(mode : Mode) -> 'ImageProvider': pass
 