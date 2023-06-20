import functools
import os.path as path
from os import mkdir,listdir,system,remove,link
import shutil
from typing import Any, Generator, List,Dict, Union, Tuple
from supported_variables.utils.utils import default_preprocessing
from utils.config import Config
from utils.logger import Logger,_Logger
if __name__ == "__main__" :
    from output_folder import OutputFolder
else :
    from file_managers.output_folder import OutputFolder

from utils.import_cdo import cdo
from netCDF4 import Dataset


class VariableNotFoundError(Exception):pass


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
            return dest,cache[files]
        else :
            output = f(files,output_file_name,output_folder)
            cache[files] = output
            return output,output
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
    
    
    def clusterize(self):
        cluster_file = {}
        self.cluster = {}
        self.file_cluster_binder = {}
        groups = {}
        uid = 1
        for id in self.io_bind.keys():
            if id in self.black_list and self.black_list[id] == True:
                continue
            
            for variable,binder in self.io_bind[id].items() :
                if variable in self.black_list[id] and self.black_list[id][variable]:
                    continue
                
                if id not in self.cluster :
                    cluster_file[id]:set = {}
                    self.cluster[id]:set = {}
                    self.file_cluster_binder[id]:set = {}
                
                if variable.preprocess == default_preprocessing:
                    files = "#".join(*binder['binder'].values())
                    if files in groups:
                        groups[files].extend(binder['binder'].keys())
                    else :
                        groups[files] = [*binder['binder'].keys()]
                        
        for id in cluster_file:
            for key in groups:
                for value in groups[key]:
                    cluster_file[id][value] = uid  
                uid += 1
            for name in cluster_file[id]:
                uid = cluster_file[id][name]
                self.cluster[id][name] = [n for n,v in cluster_file[id].items() if v == uid]

                    
            
    
    def iter_id(self) : 
        for id in self.io_bind.keys():
            if id in self.black_list and self.black_list[id] == True:
                continue
            else :
                yield id
            
    def iter_variables_from(self,id):
        for variable,binder in self.io_bind[id].items() :
            if id in self.black_list[id] and self.black_list[id][variable]:
                continue
            
            output_folder = binder['folder']
            
            def bind(id):
                for nc_var_name,files in binder['binder'].items():
                    # FILE REGEX
                    if type(files) is set:
                        output_file_name = f"{id}.{variable.name}.nc"
                        files = "#@#".join(file for file in files)
                        input_file,real = FileManager.__mergetime(files,output_file_name,output_folder)
                    # FILE DESCRIPTOR
                    elif type(files) is str:
                        input_file,real = files,files
                    # FILE SUM
                    else :
                        output_file_name = f"{id}.{variable.name}.nc"
                        files = "#@#".join(file for file in files)
                        input_file,real = FileManager.__concatenate(files,output_file_name,output_folder)
                    if nc_var_name in self.cluster[id]:
                        self.file_cluster_binder[id][input_file] = (real,self.cluster[id][nc_var_name])    
                    
                    yield input_file,nc_var_name
            yield variable,output_folder,bind
            
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
            if not path.isfile(tmp_path):
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
    def __mount_folder(input_folder:str,output:str,config:Config,variables,ids) -> 'FileManager':
        main_folder = FileManager.__mount_output(output)
        if ids is None:
            raise Exception("Experiment ids must be specified")
        io_bind = {id:{variable:{'binder':{},'folder':None} for variable in variables} for id in ids} 
        
        black_list = {}
        
        for id in ids:
            variables_black_list = {}
            for variable in variables:
                out_folder_id = main_folder.append(id)
                out_folder_id.mount()
                io_bind[id][variable]['folder'] = out_folder_id
                try :
                    for input_files,nc_var_name in config.look_up(input_folder=input_folder,id=id,variable=variable):
                        io_bind[id][variable]['binder'][nc_var_name] = input_files
                except :
                    variables_black_list[variable] = True
                    Logger.console().warning(f"variable {variable.name} will not be processed for id {id}")
            black_list[id] = variables_black_list
            if len(variables_black_list) == len(variables) :
                black_list[id] = True
                Logger.console().warning(f"variable {id} will not be processed")
            
        return FileManager(main_folder=main_folder,io_bind=io_bind, black_list = black_list)
    
    @staticmethod
    def mount(input:str,config,variables,ids,output:str="./") -> 'FileManager':
        if not path.isdir(output):
            raise Exception(f"{output} is not a folder")
        if not path.exists(input):
            raise Exception(f"{input} does not exist")
        
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
    