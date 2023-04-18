from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict
import numpy as np
from netCDF4 import Dataset,_netCDF4
import os
from cdo import Cdo


class IncorrectVariable(Exception):pass
 
def iter(values:Tuple[Union[str,Set[str]]]):
    for value in values :
        match value :
            case value if type(value) is str:
                yield value
            case value if type(value) is set:
                yield from value
def csv(v):
    names = iter(v)
    return next(names) + "".join(f",{name}" for name in names)

@dataclass
class Dimension:
    name : str
    stored_as : Union[Set[str],str]
    def namespace(self) -> Set[str]:
        match self.stored_as :
            case name if type(self.stored_as) is str:
                return {name}
            case names if type(self.stored_as) is set:
                return names
    
@dataclass
class Variable:
    name : str
    dimensions : List[Dimension]
    stored_as : Tuple[Union[Set[str],str]] = None
    preprocess : Callable[[Dict,Union[str,List[str]]],Union[str,List[str]]] = lambda x,y:y
    process : Callable[[List[np.ndarray]],np.ndarray] = lambda x:x
    clean_with_average : bool = False
    def namespace(self) -> Tuple[Set[str]]:
        if self.stored_as is None : return set()
        def convert(stored_as:Union[Set[str],str]) -> Set[str]:
            match stored_as :
                case name if type(stored_as) is str:
                    return {name}
                case names if type(stored_as) is set:
                    return names
        return tuple(convert(s) for s in self.stored_as)
    
    def __clean_dimensions(self,variable:_netCDF4.Variable) -> np.ndarray:
        data = variable[:]
        approved = [dim.namespace() for dim in self.dimensions]
        removed = [i for i,name in enumerate(variable.dimensions) \
            if not any(name in names for names in approved)]
        removed.sort(reverse=True)
        for axis in removed:
            if self.clean_with_average :
                data = np.nanmean(data,axis=axis)
            else :
                data = np.take(data,0,axis=axis)
        return data

    def __single_open(self,file:str) -> List[List[np.ndarray]]:
        with Dataset(file,"r",format="NETCDF4") as dataset:
            variables = []
            variable_names = set(dataset.variables.keys()) - set(dataset.dimensions.keys())
            if self.stored_as is None:
                if len(variable_names) != 1:
                    raise IncorrectVariable("Too many variable : must only be one variable if no names are specified")
                variable = dataset[list(variable_names)[0]]
                variable = self.__clean_dimensions(variable)
                variables.append(variable)
            else :
                for names in self.namespace():
                    name = names & variable_names         
                    if len(name) == 0:
                        raise IncorrectVariable(f"No variables match any of the specified names {names}")
                    variable = dataset[list(name)[0]]
                    variable = self.__clean_dimensions(variable)
                    variables.append(variable)            
        return self.process(variables)
        
    def __multi_open(self,inputs:list) -> List[List[np.ndarray]]:
        variables = []
        for input in inputs :
            match input:
                case file if type(input) is str:
                    variables.append(self.__single_open(file))
                case files if type(input) is list:
                    variables.extend(self.__multi_open(files))
        return variables
    
    @staticmethod
    def exec_preprocessing(files:list,selected_variable:str,output_dir:str,preprocess:Callable,extra:dict):
        cdo = Cdo()
        output_files = []
        for input in files :
            #name = os.path.splitext(os.path.basename(input))[0]
            output = os.path.join(output_dir,os.path.basename(input))
            preprocessed = preprocess(cdo,selected_variable,input,output,extra)
            if type(preprocessed) is str:
                preprocessed = [preprocessed]
            output_files.append(preprocessed)
        return output_files
    
    def open(self,input:Union[str,List[str]],args:dict,save:Callable[[List[str]],None]) -> List[np.ndarray]:
        selected_variable = csv(self.stored_as)
        
        if type(input) is str:
            input = [input]
        output_dir = args["env"].path_tmp_netcdf(args["expId"],"")
        
        preprocessed_input = Variable.exec_preprocessing(input,selected_variable,output_dir,self.preprocess,args)
        preprocessed_input = save(preprocessed_input)
        
        match preprocessed_input:
            case file if type(preprocessed_input) is str:
                return self.__single_open(file)
            case files if type(preprocessed_input) is list:
                return self.__multi_open(files)
                

if __name__ == "__main__" :
    time = Dimension(name="time",stored_as="t")
    latitude = Dimension(name="latitude",stored_as={"latitude","latitude_1"})
    longitude = Dimension(name="longitude",stored_as="longitude")
    
    variable = Variable(name="tas",\
        stored_as=("iceconc_mm_srf",),\
        dimensions=[time,latitude,longitude])

    #variable.open("./variables/test.nc",{})
    
            
    for file in os.listdir("../"):
        print(file)
        
    
    #print([x.shape for x in variable.open("./variables/test.nc",{})])
    #print(variable.open("./variables/test.nc")[0,:10,:10])
    pass