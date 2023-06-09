from typing import List
import numpy as np
import os.path as path
from utils.converters.providers.default_provider import ImageProvider
from utils.converters.utils.channel import Channel
from utils.converters.utils.utils import Mode,Extension
from PIL import Image as img

from utils.metadata.metadata import Metadata

class WEBP_Provider(ImageProvider):
    
    def save(self,filename:str,channels : List[Channel],metadata:Metadata) -> str:
        image:np.ndarray = ImageProvider.reduce(channels,self.mode,self.encoding)
        
        file_path = path.join(f"{filename}.{self.extension.value}")
        
        image : img.Image = img.fromarray(image, self.mode.name)
        image.save(file_path , format='webp',lossless = self.lossless)
        return file_path
    
    @staticmethod
    def build(mode : Mode, lossless:bool) -> 'WEBP_Provider':
        return WEBP_Provider(
            encoding=np.int8,
            extension=Extension.WEBP,
            mode=mode,
            lossless = lossless
        )