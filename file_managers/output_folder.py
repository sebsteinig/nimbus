from dataclasses import dataclass
import os.path as path
from os import mkdir
from typing import Union


@dataclass
class OutputFolder:
    main_dir : str
    out_dir  : str
    tmp_dir  : str
    name     : str = None
    
    def append(self,name:str):
        if self.name is None:
            return OutputFolder(self.main_dir,self.out_dir,self.tmp_dir,name)
        return OutputFolder(self.main_dir,\
            path.join(self.out_dir,self.name),\
            path.join(self.tmp_dir,self.name),\
            name)
    
    def out(self) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out_dir,self.name)
    
    def tmp(self) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.tmp_dir,self.name)
    
    def out_png(self)  -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out(),"png")
    
    def out_log(self)  -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out(),"log")
    
    def out_nc(self) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out(),"netcdf")
    
    def tmp_png(self) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.tmp(),"png")
    
    def tmp_nc(self) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.tmp(),"netcdf")
    
    def out_png_file(self,file_name:str) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out_png(),file_name)
    
    def out_nc_file(self,file_name:str) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.out_nc(),file_name)
    
    def tmp_png_file(self,file_name:str) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.tmp_png(),file_name)
    
    def tmp_nc_file(self,file_name:str) -> Union[str,None]:
        if self.name is None:
            return None
        return path.join(self.tmp_nc(),file_name)
    
    
    def mount(self):
        self.mount_folder()
        if not path.isdir(self.out_png()):
            mkdir(self.out_png())
        if not path.isdir(self.out_nc()):
            mkdir(self.out_nc())
        if not path.isdir(self.tmp_png()):
            mkdir(self.tmp_png())
        if not path.isdir(self.tmp_nc()):
            mkdir(self.tmp_nc())
            
                
    def mount_folder(self):
        if self.name is None: return
        if not path.isdir(self.out()):
            mkdir(self.out())
        if not path.isdir(self.tmp()):
            mkdir(self.tmp())
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)