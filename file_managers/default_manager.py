import functools
import os.path as path
from os import mkdir,listdir,system,remove,link
import shutil
from typing import Any, Generator, List,Dict, Union, Tuple
from utils.config import Config
from utils.logger import Logger,_Logger
if __name__ == "__main__" :
    from output_folder import OutputFolder
else :
    from file_managers.output_folder import OutputFolder

from utils.import_cdo import cdo

def file_name(filepath:str)->str:
    return path.basename(filepath)

def assert_nc_extension(file:str):
    return path.basename(file).split(".")[-1] == "nc"

def memoize(f):
    cache = {}
    def memoized(files,output_file_name,output_folder):
        if files in cache:
            dest = output_folder.tmp_nc_file(output_file_name)
            if not path.isfile(dest):
                link(cache[files],dest)
            return dest
        else :
            output = f(files,output_file_name,output_folder)
            cache[files] = output
            return output
    return memoized
        


class FileManager:
    def __init__(self,main_folder:OutputFolder,io_bind:Dict[str,Dict[Any,Dict[str,Tuple[OutputFolder,Union[str,List[str]]]]]], black_list : dict):
        self.main_folder = main_folder
        self.io_bind = io_bind
        self.black_list = black_list
    
    def __enter__(self):
        return self
    
    def __exit__(self,*args,**kwargs):
        if path.exists(self.main_folder.tmp_dir):
            shutil.rmtree(self.main_folder.tmp_dir)
        
    
    def iter_variables(self,note,file_manager,hyper_parameters,config) : 
        for variable in self.io_bind.keys():
            if variable in self.black_list and self.black_list[variable] == True:
                continue
            else :
                yield (note,file_manager,hyper_parameters,config,variable)
            
    def iter_id_from(self,variable):
        for id,binder in self.io_bind[variable].items() :
            if id in self.black_list and self.black_list[id]:
                continue
            
            output_folder = binder['folder']
            
            def iter():
                for nc_var_name,files in binder['binder'].items():
                    # FILE REGEX
                    if type(files) is set:
                        output_file_name = f"{id}.{variable.name}.nc"
                        files = "#@#".join(file for file in files)
                        input_file = FileManager.__mergetime(files,output_file_name,output_folder)
                    # FILE DESCRIPTOR
                    elif type(files) is str:
                        input_file = files
                    # FILE SUM
                    else :
                        output_file_name = f"{id}.{variable.name}.nc"
                        files = "#@#".join(file for file in files)
                        input_file = FileManager.__concatenate(files,output_file_name,output_folder)
                    yield input_file,nc_var_name
            yield id,output_folder,iter
            
    @memoize
    def __concatenate(files:List[str],output_file_name,output_folder):
        files = files.split("#@#")
        tmp_files = []
        for file in files:
            tmp_path = output_folder.tmp_nc_file(file_name(file).replace(".nc",".tmp.nc"))
            system(f"ncatted -a valid_min,,d,, -a valid_max,,d,, {file} {tmp_path}")
            tmp_files.append(tmp_path)
            
        output_path = output_folder.tmp_nc_file(output_file_name)
        cdo.cat(input = tmp_files, output = output_path)
        for tmp_path in tmp_files:
            remove(tmp_path)
        return output_path
    
    @memoize     
    def __mergetime(files:List[str],output_file_name,output_folder):
        files = files.split("#@#")
        tmp_files = []
        for file in files:
            tmp_path = output_folder.tmp_nc_file(file_name(file).replace(".nc",".tmp.nc"))
            system(f"ncatted -a valid_min,,d,, -a valid_max,,d,, {file} {tmp_path}")
            tmp_files.append(tmp_path)
            
        output_path = output_folder.tmp_nc_file(output_file_name)
        cdo.mergetime(input = tmp_files, output = output_path)
        for tmp_path in tmp_files:
            remove(tmp_path)
        return output_path
    @staticmethod
    def __mount_output(output:str):
        main = path.join(output,"nimbus_outputs")
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
    def __mount_file(input:str,output:str,config:Config,variables,ids) -> 'FileManager':
        if not assert_nc_extension(input):
            raise Exception(f"{input} is not a netCDF file")
        
        main_folder = FileManager.__mount_output(output)
        out_folder = main_folder.append("user")
        
        out_folder.mount()
        
        shutil.copyfile(input, out_folder.tmp_nc_file(file_name(input)))
        
        supported_variables = {}
        for name,sv in config.supported_variables.items():
            for v in variables:
                if name == v.name:
                    supported_variables[v] = [x[1] for x in sv.nc_file_var_binder]
        
        name = path.splitext(input)[0]
        
        io_bind = {variable:{name:{var_name:(out_folder,input) for var_name in supported_variables[variable] }} for variable in variables} 
        
        return FileManager(main_folder=main_folder,io_bind=io_bind)
    
    @staticmethod
    def __mount_folder(input_folder:str,output:str,config:Config,variables,ids) -> 'FileManager':
        main_folder = FileManager.__mount_output(output)
        if ids is None:
            raise Exception("Experiment ids must be specified")
        io_bind = {variable:{id:{'binder':{},'folder':None} for id in ids} for variable in variables} 
        
        black_list = {}
        
        for variable in variables:
            ids_black_list = {}
            for id in ids:
                out_folder_id = main_folder.append(id)
                out_folder_id.mount()
                io_bind[variable][id]['folder'] = out_folder_id
                try :
                    for input_files,nc_var_name in config.look_up(input_folder=input_folder,id=id,variable=variable):
                        io_bind[variable][id]['binder'][nc_var_name] = input_files
                except :
                    ids_black_list[id] = True
                    Logger.console().warning(f"experiment {id} will not be processed for variable {variable.name}")
            black_list[variable] = ids_black_list
            if len(ids_black_list) == len(ids) :
                black_list[variable] = True
                Logger.console().warning(f"variable {variable.name} will not be processed")
            
        return FileManager(main_folder=main_folder,io_bind=io_bind, black_list = black_list)
    
    @staticmethod
    def mount(input:str,config,variables,ids,output:str="./") -> 'FileManager':
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
    