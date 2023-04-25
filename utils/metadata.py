"""
model name
history (list of all commands/pre-processing done to get from original input netcdf to input used for PNG converter
version number (version of netcdf2PNG converter used)

original variable units (in original netCDF)
original xsize (in original netCDF)
original ysize (in original netCDF)

original variable long name (in original netCDF)
variable unit (either the same as in the input data or e.g. changed from C to K)
variable name (as used in ClimateArchive)
original variable name (in original netCDF)
original gridtype (in original netCDF)
timesteps (number of timesteps in PNG)
xsize (number of longitudes for each level/timestep in PNG)
ysize (number of latitudes for each level/timestep in PNG)
levels (number of vertical levels in PNG)
xfirst (first longitude value in degrees in PNG)
xinc (longitude spacing in degrees in PNG)
yfirst (first latitude value in degrees in PNG)
yinc (latitude spacing in degrees in PNG)

created at (timestamp when PNG was created)
resolution
"""
from dataclasses import dataclass
from PIL.PngImagePlugin import PngInfo

@dataclass
class Metadata:
    metadataPng : PngInfo
    model_name : str | None = None
    variable_name: str | None= None
    std_name: str | None= None
    variable_unit : str | None= None
    or_variable_name : str | None= None
    or_variable_long_name : str | None= None
    or_variable_unit : str | None= None
    or_grid_type: str | None= None
    or_xsize : int | None= None
    or_ysize : int | None= None
    history : str | None= None
    netcdf2png_version : str | None= None
    xsize : int | None= None
    ysize : int | None= None
    levels : int | None= None
    timesteps : int | None= None
    xfirst : float | None= None
    xinc : float | None= None
    yfirst :float | None= None
    yinc : float | None= None
    created_at : str | None= None
    min_max : str | None= None
    resolution : float | None= None

    def getMetadata(self, date, minmax):
        self.created_at = date
        self.min_max = minmax
        self.metadataPng.add_text("created_at", self.created_at)
        self.metadataPng.add_text("min_max", self.min_max)
        return self.metadataPng

    def __init__(self, variableName, variable):
        self.variable_name = variableName
        self.or_variable_name = variable.name
        self.or_variable_long_name = variable.long_name
        self.variable_unit = variable.units
        self.std_name = variable.standard_name
        self.metadataPng = PngInfo()
        self.metadataPng.add_text("variable_name", self.variable_name)
        self.metadataPng.add_text("or_variable_name", self.or_variable_name)
        self.metadataPng.add_text("or_variable_long_name", self.or_variable_long_name)
        self.metadataPng.add_text("variable_unit", self.variable_unit)
        self.metadataPng.add_text("std_name", self.std_name)

    def set_grid(self, grid):
        self.or_grid_type = grid.category
        longitude = grid.axis[0]
        latitude = grid.axis[1]
        self.xinc = longitude.step
        self.yinc = latitude.step
        self.xfirst = longitude.bounds[0]
        self.yfirst = latitude.bounds[0]
        self.xsize = grid.points[1][0]
        self.ysize = grid.points[1][1]
        self.metadataPng.add_text("or_grid_type", self.or_grid_type)
        self.metadataPng.add_text("xinc", str(self.xinc))
        self.metadataPng.add_text("yinc", str(self.yinc))
        self.metadataPng.add_text("xfirst", str(self.xfirst))
        self.metadataPng.add_text("yfirst", str(self.yfirst))
        self.metadataPng.add_text("xsize", str(self.xsize))
        self.metadataPng.add_text("ysize", str(self.ysize))
    
    def set_vertical(self, vertical):
        self.levels = vertical.levels
        self.metadataPng.add_text("levels", str(self.levels))

    def set_time(self, time):
        self.timesteps = time.step
        self.metadataPng.add_text("timesteps", str(self.timesteps))

    #TODO
    def set_resolution(self, resolution):
        self.resolution = resolution
        self.metadataPng.add_text("resolution", str(self.resolution))

    #TODO
    def set_history(self, history):
        self.history = history
        #self.metadataPng.add_text("history", str(self.history))

    #TODO
    def set_original_dimensions(self, xsize, ysize, unit):
        self.or_xsize = xsize
        self.or_ysize = ysize
        self.or_variable_unit = unit
        self.metadataPng.add_text("or_xsize", str(self.or_xsize))
        self.metadataPng.add_text("or_ysize", str(self.or_ysize))
        self.metadataPng.add_text("or_variable_unit", str(self.or_variable_unit))

    #TODO
    def set_nc2pngVersion(self, version):
        self.netcdf2png_version = version
        self.metadataPng.add_text("netcdf2png_version", str(self.netcdf2png_version))
    
    #TODO
    def set_model_name(self, name):
        self.model_name = name
        self.metadataPng.add_text("model_name", str(self.model_name))


if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)