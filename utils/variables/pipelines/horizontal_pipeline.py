from dataclasses import dataclass,replace
import math
from typing import Tuple
from utils.logger import Logger
from utils.variables.info import Grid, Info
from cdo import Cdo
import os.path as path
from os import remove

cdo = Cdo()

@dataclass
class HorizontalPipeline:
    resolution:Tuple[float,float]
    grid:Grid
    
    """
        execute the pipeline 
        param :
            file : str,
            info : Info
        return :
            Tuple[str,Info]
    """
    def exec(self,file:str,info:Info) -> Tuple[str,Info]:
        
        output_file = self.to_lonlat(file)
        output_file = self.resize(output_file)

        sinfo = cdo.sinfo(input=output_file)
        info = Info.parse(sinfo)
        return output_file,info
    
    """
        exclude the non lonlat grid
        param :
            
        return :
            None
    """
    def to_lonlat(self,file:str):
        if self.grid.category != "lonlat":
            raise Exception("UNIMPLETED : can't change grid resolution, only lonlat grid are supported")
        else :
            return file
        
    """
        perform the resizing of a file, by regrid the grid and writting the description
        in a file, remapping with cdo in a output file and deleting the description file
        param :
            file : str
        return :
            str
    """
    def resize(self,file):
        grid = self.compute()
        desc = HorizontalPipeline.grid_description_str(HorizontalPipeline.grid_description(grid))
        
        folder = path.dirname(file)
        resize_file_txt_name = path.basename(file).replace(".nc",".resize.txt")
        resize_file_txt_path = path.join(folder,resize_file_txt_name)
        
        with open(resize_file_txt_path,'w') as f:
            f.write(desc)
            
        res_suffixe = f".rx{grid.axis[0].step}.ry{grid.axis[1].step}"
        output_file = file.replace(".nc",f"{res_suffixe}.nc")
        cdo.remapnn(resize_file_txt_path,input=file,output=output_file)
        remove(resize_file_txt_path)
        return output_file
    
    """
        regrid the grid with the chosen resolution
        param :
            
        return :
            Grid
    """
    def compute(self) -> Grid:
        grid = replace(self.grid)
        
        for axis in (0,1):
            if self.resolution[axis] is None:
                continue
            new_step = abs(self.resolution[axis])
            
            prev_size = self.grid.points[1][axis] - 1
            prev_first = self.grid.axis[axis].bounds[0]
            prev_last = self.grid.axis[axis].bounds[1]
            prev_step = self.grid.axis[axis].step
            
            new_step *= (prev_last - prev_first)/abs(prev_first - prev_last)
            
            new_size = math.floor(abs( prev_size * prev_step / new_step ))
            sizes = list(grid.points[1])
            sizes[axis] = new_size + 1
            grid.points = (grid.points[0],tuple(sizes))
            grid.axis[axis].step = new_step
        grid.points = (grid.points[1][0] * grid.points[1][1],(grid.points[1][0] , grid.points[1][1]))
        
        return grid

    """
        build a HorizontalPipeline with the correct input,
        if no pipeline is needed a idle object will be return that does nothing
        param :
            resolution : Tuple[float,float]
            grid : Grid
        return :
            HorizontalPipeline
    """
    @staticmethod
    def build(resolution:Tuple[float,float],grid:Grid) -> 'HorizontalPipeline':
        if resolution == (None,None):
            class IDLE:
                def exec(self,file:str,info:Info) -> Tuple[str,Info]:
                    return file,info
            return IDLE()
        return HorizontalPipeline(resolution=resolution,grid=grid)
    
    """
        transforn a dict of grid description into a text that will be written into a file
        param :
            grid : dict
        return :
            str
    """
    @staticmethod
    def grid_description_str(grid:dict) -> str:
        return "".join(f"{key} = {value}\n" for key,value in grid.items())
    
    """
        trnasform a grid into a dict with the description needed by cdo remap
        param :
            grid : Grid
        return :
            dict
    """
    @staticmethod
    def grid_description(grid:Grid) -> dict:
        return {
            'gridtype'  : grid.category,
            'xsize'     : grid.points[1][0],
            'ysize'     : grid.points[1][1],
            'xfirst'    : grid.axis[0].bounds[0],
            'xinc'      : grid.axis[0].step,
            'yfirst'    : grid.axis[1].bounds[0],
            'yinc'      : grid.axis[1].step,
        }
    