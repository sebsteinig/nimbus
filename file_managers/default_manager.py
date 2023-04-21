import os.path as path
from os import mkdir,listdir
import shutil
from typing import List,Dict

if __name__ == "__main__" :
    from output_folder import OutputFolder
else :
    from file_managers.output_folder import OutputFolder

def file_name(filepath:str)->str:
    return path.basename(filepath)

def assert_nc_extension(file:str):
    return path.basename(file).split(".")[-1] == "nc"

class FileManager:
    def __init__(self,input,output:Dict[str,OutputFolder]):
        self.input = input
        self.output = output
    
    def get_output(self,input) -> OutputFolder:
        return self.output[input]
        
    
    def iter(self):
        for key,value in self.output.items() :
            yield key,value
    
    def clean(self):
        for key,value in self.output.items() :
            FileManager.__clean(value.out_dir)
        
    @staticmethod
    def __clean(folder:str):
        if path.exists(folder):
            shutil.rmtree(folder)
    
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
    def __mount_file(input:str,output:str):
        if not assert_nc_extension(input):
            raise Exception(f"{input} is not a netCDF file")
        
        out_folder = FileManager.__mount_output(output)
        out_folder = out_folder.append("user")
        
        out_folder.mount()
        
        shutil.copyfile(input, out_folder.tmp_nc_file(file_name(input)))
        
        return FileManager(input,{input:out_folder})
    
    @staticmethod
    def __mount_folder(input:str,output:str):
        out_folder = FileManager.__mount_output(output)
        user = out_folder.append("user")
        user.mount_folder()
        user = user.append(path.basename(path.normpath(input)))
        user.mount()
        out_folder_dict = {}
        
        def mount(folder:str,out_folder):
            for file in listdir(folder):
                file_path = path.join(folder, file)
                if path.isdir(file_path):
                    sub = out_folder.append(file)
                    mount(file_path,sub)
                elif path.isfile(file_path) and assert_nc_extension(file_path):
                    out_folder_dict[file_path] = out_folder
                    
        
        mount(input,user)
        
        for key,value in out_folder_dict.items():
            value.mount()
            
        return FileManager(input,out_folder_dict)
    
    
    @staticmethod
    def mount(input:str,output:str="../"):
        if not path.isdir(output):
            raise Exception(f"{output} is not a folder")
        if not path.exists(input):
            raise Exception(f"{input} does not exist")
        
        match input:
            case file if path.isfile(input):
                return FileManager.__mount_file(input,output)
            case folder if path.isdir(input):
                return FileManager.__mount_folder(input,output)    
            
            
            
            
if __name__ == "__main__" :
    fm = FileManager.mount("./testfolder","/home/willem/workspace/internship-climate-archive/")
    for input,output in fm.iter():
        print(f"Input : {input}")
        print(f"\t{output}")