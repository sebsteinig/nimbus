from dataclasses import dataclass
from PIL.PngImagePlugin import PngInfo
from typing import Union, List, Any, Callable
import json

@dataclass
class VariableSpecificMetadata:
    variable_name: Union[str , None]= None
    original_variable_name : Union[str  , None]= None       #original variable name in original netCDF
    original_variable_long_name : Union[str, None]=None     #original variable long name in original netCDF
    std_name: Union[str, None]=None                         #standard variable name
    model_name : Union[str,None] = None
    variable_unit : Union[str, None]=None                   #either the same as in the input data or e.g. changed from C to K
    original_variable_unit : Union[str, None]=None          #original variable units in original netCDF
    history : Union[str, None]= None                        #list of all commands/pre-processing done to get from original input netcdf to input used for image converter
    original_grid_type: Union[str, None]=None               #gridtype in original netCDF
    original_xsize : Union[str, None]=None                  #original number of longitudes for each level/timestep in original netCDF
    original_ysize : Union[str, None]=None
    
#the data in this class are the same when there are multiple variables
@dataclass
class GeneralMetadata:
    xsize : Union[int, None]=None                   #number of longitudes for each level/timestep in image
    ysize : Union[int, None]=None                   #number of latitudes for each level/timestep in image
    levels : Union[int, None]=None                  #number of vertical levels in image
    timesteps : Union[int, None]=None               #number of timesteps in image
    xfirst : Union[float, None]=None                #first longitude value in degrees in image
    xinc : Union[float, None]=None                  #longitude spacing in degrees in image
    yfirst :Union[float, None]=None
    yinc : Union[float, None] =None
    created_at : Union[str  , None] = None          #timestamp when image was created
    min_max : Union[str  , None] = None             #min and max values for each variable and dimension
    resolution : Union[str , None] = None           #image resolution
    netcdf2png_version : Union[str, None] = None    #version of netcdf2image converter used
    nan_value_encoding : Union[ int, None] = None   #value in image that replace nan values (0 or 255)
    threshold : Union[ int, None] = None            #threshold used to normalize input

class Metadata:
    dataVariables : List[VariableSpecificMetadata] = []
    dataGeneral : Union[GeneralMetadata, None] = None

    def get_metadata(self, date, minmax, format = "png"):
        self.dataGeneral.created_at = date
        self.dataGeneral.min_max = minmax
        if format == "png":
            return self.get_metadata_png()

    def get_metadata_png(self):
        metadataPng = PngInfo()
        metadataPng.add_text("variables", str(json.dumps(self.get_list_variables())))
        metadataPng = self.add_for_class_attributes(GeneralMetadata, self.dataGeneral, metadataPng, self.method_for_png)
        return metadataPng

    def get_metadata_WebP():
        pass

    @staticmethod
    def add_for_class_attributes(objClass, obj, result, function:Callable[[Any, str, Any], None]):
        for attr in objClass.__dataclass_fields__.keys():
            if getattr(obj,attr) is not None:
                function(result, attr, getattr(obj,attr))
        return result

    @staticmethod
    def method_for_png(metadataPng, key, value):
        metadataPng.add_text(key, str(value))

    @staticmethod
    def method_for_dict(dict, key, value):
        dict[key] = value

    @staticmethod
    def method_fo_WebP(metadata, key, value):
        pass

    def set_info(self, info, variable, variableName):
        grid = info.get_grid(variable.dimensions)
        data = VariableSpecificMetadata()     
        if self.dataGeneral == None:
            self.dataGeneral = GeneralMetadata()
            if info.get_time(variable.dimensions) is not None :
                self.dataGeneral.timesteps = info.get_time(variable.dimensions).step
            if info.get_vertical(variable.dimensions) is not None :
                self.dataGeneral.levels = info.get_vertical(variable.dimensions).levels
            if grid is not None :
                self.dataGeneral.xinc = grid.axis[0].step
                self.dataGeneral.yinc = grid.axis[1].step
                self.dataGeneral.xfirst = grid.axis[0].bounds[0]
                self.dataGeneral.yfirst = grid.axis[1].bounds[0]
                self.dataGeneral.xsize = grid.points[1][0]
                self.dataGeneral.ysize = grid.points[1][1]
        data.variable_name = variableName
        data.original_variable_name = variable.name
        data.std_name = variable.standard_name
        data.original_variable_long_name = variable.long_name
        data.variable_unit = variable.units
        if grid is not None :
            data.original_grid_type = grid.category
        self.dataVariables.append(data)

    def set_resolution(self, resolution):
        self.dataGeneral.resolution = str(resolution)
    
    def set_threshold(self, threshold):
        self.dataGeneral.threshold = str(threshold)
    
    def set_nan_value_encoding(self, value):
        self.dataGeneral.nan_value_encoding = str(value)

    def get_list_variables(self):
        return [self.add_for_class_attributes(VariableSpecificMetadata,\
            data, {}, self.method_for_dict) for data in self.clean_variables()]
    
    def log_for_debug(self):
        dict = {}
        dict["variables"] = self.get_list_variables()
        dict = self.add_for_class_attributes(GeneralMetadata, self.dataGeneral, dict, self.method_for_dict)        
        return json.dumps((dict), indent=2)
    
    def clean_variables(self):
        if len(self.dataVariables)<1:
            return self.dataVariables
        else:
            def are_equals(vari, var0):
                for attr in VariableSpecificMetadata.__dataclass_fields__.keys():
                    if getattr(vari, attr) != getattr(var0, attr):
                        return False
                return True
            res = [self.dataVariables[0]]
            for i in range(1, len(self.dataVariables)):
                if not are_equals(self.dataVariables[i], self.dataVariables[0]):
                    res.append(self.dataVariables[i])
            self.dataVariables = res
            return res
    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)