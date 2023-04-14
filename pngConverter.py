from typing import Any
import numpy as np
from netCDF4 import Dataset
from PIL import Image
from enum import Enum
from typing import Tuple, Callable
from dataclasses import dataclass
import os

class LatitudeNotFound(Exception):pass
class LongitudeNotFound(Exception):pass
class TimeNotFound(Exception):pass
class LongitudeNotWellDefine(Exception):pass
class LatitudeNotWellDefine(Exception):pass
class OutputVariableNotRecognized(Exception):pass

class Dimension(Enum):
    Latitude=0,
    Longitude=1,
    Time=2,


@dataclass
class Variable:
    data:Any
    meta:Any

class OutputVariable(Enum):
    Tas = "tas"
    Tas_Anomaly = "tas_anomoly"
    Pr = "pr" 
    Clt = "clt"
    Snc = "snc"
    Tos = "tos"
    MLotst = "mlotst"
    Siconc = "siconc"
    Liconc = "liconc"
    Height = "height"
    Orog = "orog"
    OceanCurrents = "oceanCurrents"
    Winds = "winds"
    
@dataclass
class OutputMeta:
    bound:Tuple[int,int]
    preprocess:Callable[[],None]
    
def getDimension(dimensions,names,error):
    for name in names:
        if name in dimensions:
            return dimensions[name]
    error()

def throw(error,message):
    def tmp():
        raise error(message)
    return tmp

class Environment:
    def __init__(self,dataset):
        self.variables = dataset.variables
        self.dimensions = dataset.dimensions
        
        self.latitude_dim = getDimension(self.dimensions,\
            ("lat","latitude"),\
            throw(LatitudeNotFound,"unexpected latitude dimension name"))
        self.longitude_dim = getDimension(self.dimensions,\
            ("lon","longitude"),\
            throw(LongitudeNotFound,"unexpected longitude dimension name"))
        self.time_dim = getDimension(self.dimensions,\
            ("month","time","t","time_counter"),\
            throw(TimeNotFound,"unexpected time dimension name"))
        self.latitude = self.get(self.latitude_dim.name)
        self.longitude = self.get(self.longitude_dim.name)
        self.time = self.get(self.time_dim.name)

        def pr_preprocessing(input,args):
            with Dataset(args.reference_file,"r",format="NETCDF4") as ref_file:
                ref_data = np.squeeze(ref_file.variables[args.variableBRIDGE][:])
                ref_data_zm = np.mean(ref_data, axis=1, keepdims=True)
                input -= ref_data_zm
        
        self.outputMeta = {
            OutputVariable.Tas : OutputMeta((-50,50),lambda input,args: input - 273.15),
            OutputVariable.Tas_Anomaly : OutputMeta((-50,50),lambda input,args: input - 273.15),
            OutputVariable.Pr : OutputMeta((0,25),pr_preprocessing),
            OutputVariable.Clt : OutputMeta((0,1),lambda x,y:x),
            OutputVariable.Snc : OutputMeta((0,1),lambda x,y:x),
            OutputVariable.Tos : OutputMeta((-2,42),lambda x,y:x),
            OutputVariable.MLotst : OutputMeta((0,1000),lambda x,y:x),
            OutputVariable.Siconc : OutputMeta((0,1),lambda x,y:x),
            OutputVariable.Liconc : OutputMeta((0,1),lambda x,y:x),
            OutputVariable.Height : OutputMeta((-5000,5000),lambda x,y:x),
            OutputVariable.Orog : OutputMeta((0,5000),lambda x,y:x),
        }
        
    def size(self,dimemsion):
        match dimemsion:
            case Dimension.Latitude:
                return self.latitude_dim.size
            case Dimension.Longitude:
                return self.longitude_dim.size
            case Dimension.Time:
                return self.time_dim.size
    def rank(self,variable,dimemsion):
        match dimemsion:
            case Dimension.Latitude:
                return variable.meta.dimensions.index(self.latitude_dim.name)
            case Dimension.Longitude:
                return variable.meta.dimensions.index(self.longitude_dim.name)
            case Dimension.Time:
                return variable.meta.dimensions.index(self.time_dim.name)
    def get(self,name):
        return Variable(self.variables[name][:],self.variables[name])

def assert_input(input, env):
    if all(x<y for x, y in zip(env.latitude.data, env.latitude.data[1:])):
        env.latitude.data = np.flip(env.latitude.data,0)
        input.data = np.flip(input.data,env.rank(input,Dimension.Latitude))
    if (np.amax(env.longitude.data) > 180) or not all(x<y for x, y in zip(env.longitude.data, env.longitude.data[1:])):
        raise LongitudeNotWellDefine("longitudes seem to be outside [-180,180]")
    


def norm(arr, norm_min, norm_max):
    return (arr - norm_min) / (norm_max - norm_min)

def preprocess(input,env,out_meta,args):
    out_meta.preprocess(input,args)


   
def convert(input,env,out_meta):
    output = np.zeros( ( env.size(Dimension.Latitude), env.size(Dimension.Longitude) * env.size(Dimension.Time) ) )
    for index in range(env.size(Dimension.Time)):
        output[:,index* env.size(Dimension.Longitude)  : ((index+1)* env.size(Dimension.Longitude) )] = \
            norm(input.data[index,:,:], out_meta.bound[0],  out_meta.bound[1]) * 255
    return output

    
def save(output,output_file):
    out = np.squeeze(output)
    img_ym = Image.fromarray(np.uint8(out) , 'L')
    img_ym.save(output_file + ".png")

def clean(output):
    output[output > 255] = 255
    output[output < 0] = 0
    output[np.isnan(output)] = 0
    return output
    
def convert_to_png(input_file,expId,variable_name,output_variable,output_dir):
    with Dataset(input_file,"r",format="NETCDF4") as dataset:
        print(f"converting {input_file}")
        env = Environment(dataset)
        input = env.get(variable_name)
        assert_input(input,env)
        if not output_variable in OutputVariable._value2member_map_:
            raise OutputVariableNotRecognized(f"{output_variable} is not valid output variable")
        out_meta = env.outputMeta[OutputVariable(output_variable)]
        preprocess(input,env,out_meta,None)
        
        mean = np.nanmean(input.data, axis=env.rank(input,Dimension.Time))
        mean = norm(mean, out_meta.bound[0],  out_meta.bound[1]) * 255
        mean = clean(mean)
        
        output = convert(input,env,out_meta)
        output = clean(output)
        
        period = "m" if env.size(Dimension.Time) == 12 else "y"
        
        output_file = f"{expId}.{output_variable}.{period}"
        output_file = os.path.join(output_dir,output_file)
        save(output, output_file + ".steps")
        save(mean, output_file + ".mean")
      


if __name__ == "__main__":
    input_file = "test.nc"
    expId = "texpa1"
    variable_name = "temp_mm_uo"
    output_variable = "tos"
    convert_to_png(input_file,expId,variable_name,output_variable,"./")