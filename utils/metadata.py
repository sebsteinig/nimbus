from dataclasses import dataclass
from PIL.PngImagePlugin import PngInfo
from typing import Dict, Union, List, Any, Callable
import json
from utils.variables.info import Info

"""
    Data Class VariableSpecificMetadata
    data that are specific to variable
"""
@dataclass
class VariableSpecificMetadata:
    original_variable_name : str= None          #original variable name in original netCDF
    original_variable_long_name : str=None      #original variable long name in original netCDF
    std_name: str=None                          #standard variable name
    history : str= None                         #TODO list of all commands/pre-processing done to get from original input netcdf to input used for image converter
    model_name : str = None                     #TODO
    variable_unit : str=None                   #either the same as in the input data or e.g. changed from C to K
    original_variable_unit : str=None          #TODO original variable units in original netCDF
    original_grid_type: str=None               #TODO gridtype in original netCDF
    original_xsize : str=None                  #TODO original number of longitudes for each level/timestep in original netCDF
    original_ysize : str=None                  #TODO
    original_xinc : str=None                  
    original_yinc : str=None
    min_max : list = None             #min and max values for each variable and dimension
    
    """
        function that sets values to attributes
        param :
            kargs : dict (attribute_name = "value")
        return : None
    """
    def extends(self,**kargs) -> None:
        types = self.__annotations__
        for key,value in kargs.items():
            if key in self.__dict__:
                self.__dict__[key] = types[key].__call__(value)
        
    """
        function that returns the data of the class as a dict
        return : dict
    """
    def to_dict(self) -> dict:
        return dict(self.__dict__.copy())
    
    """
        function that initializes a VariableSpecificMetadata object
        param : 
            kargs : dict (with attribute names and value)
        return : 
            the VariableSpecificMetadata instance
    """
    @staticmethod
    def build(**kargs) -> 'VariableSpecificMetadata':
        vsm = VariableSpecificMetadata()
        types = vsm.__annotations__
        for key,value in kargs.items():
            if key in vsm.__dict__:
                vsm.__dict__[key] = types[key].__call__(value)
        return vsm
    
"""
    Data Class GeneralMetadata
    the data in this class are the same when there are multiple variables.
"""
@dataclass
class GeneralMetadata:
    variable_name: str= None
    xsize : int=None                   #number of longitudes for each level/timestep in image
    ysize : int=None                   #number of latitudes for each level/timestep in image
    levels : int=None                  #number of vertical levels in image
    timesteps : int=None               #number of timesteps in image
    xfirst : float=None                #first longitude value in degrees in image
    xinc : float=None                  #longitude spacing in degrees in image
    yfirst :float=None
    yinc : float =None
    created_at : str= None          #timestamp when image was created
    resolution : str = None           #image resolution
    version : str = None    #TODO version of netcdf2image converter used
    nan_value_encoding :int= None   #value in image that replace nan values (0 or 255)
    threshold :int= None            #threshold used to normalize input

    """
        function that sets values to attributes
        param :
            kargs : dict (attribute_name = "value")
        return :
            None
    """
    def extends(self,**kargs):
        types = self.__annotations__
        for key,value in kargs.items():
            if key in self.__dict__:
                self.__dict__[key] = types[key].__call__(value)
        
    
    """
    function that returns the data of the class as a dict
    return : dict
    """
    def to_dict(self):
        return dict(self.__dict__.copy())
    
    """
    function that initializes a GeneralMetadata object
    param : 
        kargs : dict (with attribute names and value)
    return : 
        the GeneralMetadata instance
    """
    @staticmethod
    def build(**kargs) -> 'GeneralMetadata':
        gm = GeneralMetadata()
        types = gm.__annotations__
        for key,value in kargs.items():
            if key in gm.__dict__:
                gm.__dict__[key] = types[key].__call__(value)
        return gm

"""
    Class Metadata
    This class contains all the information that will be in the image metadata.
"""
class Metadata:
    vs_metadata : List[VariableSpecificMetadata] = []
    general_metadata : Union[GeneralMetadata, None] = GeneralMetadata()

    """
        call the extends function from GeneralMetadata
        param :
            kargs : dict
        return :
            None
    """
    def extends(self,**kargs):
        self.general_metadata.extends(**kargs)

    """
        function that add new VariableSpecificMetadata in the vs_metadata list
        param :
            vs_metadata : list
        return :
            None
    """
    def push(self,vs_metadata : List[VariableSpecificMetadata] ):
        self.vs_metadata.extend(vs_metadata)

    """
        returns the metadata as a string for the log
        param :
            None
        return :
            str
    """
    def log(self) -> str:
        return json.dumps(self.to_dict(),indent=2)
    def to_dict(self):
        res = {}
        res.update(self.general_metadata.to_dict())
        res["variables"] = []
        for m in self.vs_metadata:
            res["variables"].append(m.to_dict())
            
        return res
        

if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)