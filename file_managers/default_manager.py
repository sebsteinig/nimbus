import os.path as path
from os import mkdir,listdir,system,remove
import shutil
from typing import Any, Generator, List,Dict, Union, Tuple
from utils.config import Config
from utils.logger import Logger,_Logger
from cdo import Cdo
if __name__ == "__main__" :
    from output_folder import OutputFolder
else :
    from file_managers.output_folder import OutputFolder
    
cdo = Cdo()

def file_name(filepath:str)->str:
    return path.basename(filepath)

def assert_nc_extension(file:str):
    return path.basename(file).split(".")[-1] == "nc"

class FileManager:
    def __init__(self,io_bind:Dict[str,Dict[Any,Dict[str,Tuple[OutputFolder,Union[str,List[str]]]]]], missing_ids : List[str]):
        self.io_bind = io_bind
        self.missing_ids = missing_ids

    
    def iter(self) -> Generator[Tuple[List[Tuple[str,str]],OutputFolder,Any],None,None]:
        for variable,value in self.io_bind.items():
            for id,value_2 in value.items():
                if id in self.missing_ids:
                    continue                
                input_files = []
                for nc_var_name,value_3 in value_2.items():
                    output_folder,files = value_3
                    if len(files) == 1 :
                        input_file = files[0]
                    elif type(files) is str:
                        input_file = files
                    else :
                        output_file_name = f"{id}.{variable.name}.nc"
                        input_file = FileManager.__concatenate(files,output_file_name,output_folder)
                    input_files.append((input_file,nc_var_name))
                yield input_files,output_folder,variable,id
        
    @staticmethod
    def __concatenate(files:List[str],output_file_name,output_folder):
        tmp_files = []
        for file in files:
            """
            from netCDF4 import Dataset,_netCDF4
            with Dataset(file,"r",format="NETCDF4") as dataset:
                print(dataset.variables.keys())
            """
            tmp_path = output_folder.tmp_nc_file(file_name(file).replace(".nc",".tmp.nc"))
            system(f"ncatted -a valid_min,,d,, -a valid_max,,d,, {file} {tmp_path}")
            tmp_files.append(tmp_path)
            
        output_path = output_folder.tmp_nc_file(output_file_name)
        cdo.cat(input = tmp_files, output = output_path)
        for tmp_path in tmp_files:
            remove(tmp_path)
        return output_path
    
    @staticmethod
    def __mount_output(output:str):
        main = path.join(output,"nc_to_png_outputs")
        if not path.isdir(main):
            mkdir(main)
        out = path.join(main,"output")
        if not path.isdir(out):
            mkdir(out)
        tmp = path.join(main,"tmp")
        if not path.isdir(tmp):
            mkdir(tmp)
        return OutputFolder(main_dir=main,out_dir=out,tmp_dir=tmp)

    @staticmethod
    def __mount_file(input:str,output:str,config:Config,variables,ids):
        if not assert_nc_extension(input):
            raise Exception(f"{input} is not a netCDF file")
        
        out_folder = FileManager.__mount_output(output)
        out_folder = out_folder.append("user")
        
        out_folder.mount()
        
        shutil.copyfile(input, out_folder.tmp_nc_file(file_name(input)))
        
        supported_variables = {}
        for name,sv in config.supported_variables.items():
            for v in variables:
                if name == v.name:
                    supported_variables[v] = [x[1] for x in sv.nc_file_var_binder]
        
        name = path.splitext(input)[0]
        
        io_bind = {variable:{name:{var_name:(out_folder,input) for var_name in supported_variables[variable] }} for variable in variables} 
        
        return FileManager(io_bind=io_bind)
    
    @staticmethod
    def __mount_folder(input_folder:str,output:str,config:Config,variables,ids):
        out_folder = FileManager.__mount_output(output)
        if ids is None:
            raise Exception("Experiment ids must be specified")
        io_bind = {variable:{id:{} for id in ids} for variable in variables} 
        missing_ids = []
        for id in ids:
            out_folder_id = out_folder.append(id)
            out_folder_id.mount()
            cpt = 0
            for input_files,nc_var_name,variable in config.look_up(input_folder=input_folder,id=id,variables=variables):
                io_bind[variable][id][nc_var_name] = (out_folder_id, input_files)
                cpt+=1
            if cpt ==0:
                missing_ids.append(id)
                Logger.console().warning(f"experiment {id} will not be processed")
        return FileManager(io_bind=io_bind, missing_ids = missing_ids)
    
    @staticmethod
    def mount(input:str,config,variables,ids,output:str="./"):
        if not path.isdir(output):
            raise Exception(f"{output} is not a folder")
        if not path.exists(input):
            raise Exception(f"{input} does not exist")
        
        if path.isfile(input):
            return FileManager.__mount_file(input,output,config,variables,ids)
        elif path.isdir(input):
            return FileManager.__mount_folder(input,output,config,variables,ids)    
        

    @staticmethod
    def clean(exp_ids, output):
        out_folder = FileManager.__mount_output(output)
        for id in exp_ids:
            out_folder_id = out_folder.append(id)
            if path.exists(out_folder_id.out()):
                shutil.rmtree(out_folder_id.out())
            
if __name__ == "__main__" :
    fm = FileManager.mount("./testfolder","/home/willem/workspace/internship-climate-archive/")
    for input,output in fm.iter():
        print(f"Input : {input}")
        print(f"\t{output}")
    