from typing import List
import numpy as np
import os.path as path
from utils.converters.providers.default_provider import ImageProvider
from utils.converters.utils.channel import Channel
from utils.converters.utils.utils import Mode,Extension
from PIL import Image as img
from PIL.PngImagePlugin import PngInfo
import json

from utils.metadata.metadata import Metadata

class PNG_Provider(ImageProvider):
    
    def save(self,filename:str,channels : List[Channel],metadata:Metadata) -> str:
        image:np.ndarray = ImageProvider.reduce(channels,self.mode,self.encoding)
        
        file_path = path.join(f"{filename}.{self.extension.value}")
        
        image : img.Image = img.fromarray(image, self.mode.name)
        image.save(file_path , pnginfo = self.to_png_info(metadata) , lossless = self.lossless, optimize=True , format='png')
        return file_path
    
    def to_png_info(self,metadata : Metadata) -> PngInfo:
        png_info = PngInfo()
        for key,value in metadata.to_dict().items():
            png_info.add_text(key,str(json.dumps(value)))
        return png_info
    
    @staticmethod
    def build(mode : Mode, lossless : bool) -> 'PNG_Provider':
        return PNG_Provider(
            encoding=np.int8,
            extension=Extension.PNG,
            mode=mode,
            lossless = lossless
        )