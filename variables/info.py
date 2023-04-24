"""
Grid coordinates :
1 : lonlat                   : points=7008 (96x73)
longitude : -180 to 176.25 by 3.75 degrees_east  circular
latitude : -90 to 90 by 2.5 degrees_north
2 : lonlat                   : points=6912 (96x72)
longitude_1 : -178.125 to 178.125 by 3.75 degrees_east  circular
latitude_1 : -88.75 to 88.75 by 2.5 degrees_north
Vertical coordinates :
1 : generic                  : levels=19
depth : 10 to 4885 m
2 : generic                  : levels=1
unspecified : -1 unspecified
3 : generic                  : levels=20
depth_1 : 5 to 5192.65 m
Time coordinate :
t : 1 step
RefTime =  1850-12-00 00:00:00  Units = days  Calendar = 360_day
YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss
6750-06-01 00:00:00
"""

from dataclasses import dataclass
from typing import List,Union,Set,Callable,Tuple,Dict,Type

@dataclass(eq=True, frozen=True)
class Axis:
    name   : str
    bounds : Tuple[float,float]
    step   : float
    direction : str
    
    @staticmethod
    def parse(src : str):
        sections = src.split(":")
        name = sections[0].strip()
        tmp = sections[-1].strip().split(" ")
        bounds = (float(tmp[0]),float(tmp[2]))
        step = float(tmp[4])
        direction = tmp[5]
        return Axis(bounds=bounds, direction=direction, name=name, step=step)
        
    def to_dict(self):
        return {
            'name' : self.name,
            'bounds': list(self.bounds),
            'step' : self.step,
            'direction':self.direction
        }
@dataclass(eq=True, frozen=True)
class Grid:
    category : str
    points   : Tuple[int,Tuple[int,int]]
    axis : Tuple[Axis,Axis]

    @staticmethod
    def parse(src : List[str],cursor:int):
        if src[cursor].strip()[0].isdigit():
            sections = src[cursor].split(":")
            if len(sections) > 1:
                category = sections[-2].strip()
                tmp = sections[-1].split("=")[-1].split(" ")
                size = int(tmp[0])
                shape = tuple(tmp[-1][1:-1].split("x"))
                points = (size,shape)
                axis = (Axis.parse(src[cursor+1]),Axis.parse(src[cursor+2]))
                return Grid(category=category,axis=axis,points=points)
        return None
            
    def to_dict(self):
        return {
            'category' : self.category,
            'points': [self.points[0],[int(self.points[1][0]),int(self.points[1][0])]],
            'axis' : [self.axis[0].to_dict(), self.axis[1].to_dict()]
        }

@dataclass(eq=True, frozen=True)
class Vertical:
    category : str
    name     : str
    levels   : int
    bounds   : Tuple[float,float]

    @staticmethod
    def parse(src : List[str],cursor:int):
        if src[cursor].strip()[0].isdigit():
            sections = src[cursor].split(":")
            if len(sections) > 1:
                category = sections[-2].strip()
                levels = int(sections[-1].strip().split("=")[-1])
                tmp = src[cursor+1].split(":")
                name = tmp[0].strip()
                tmp = tmp[1].strip().split(" ")
                if len(tmp) > 2:
                    bounds = (tmp[0],tmp[2])
                else :
                    bounds = (None,None)
                return Vertical(category=category,name=name,levels=levels,bounds=bounds)
        return None
    
    def to_dict(self):
        return {
            'category' : self.category,
            'name': self.name,
            'levels':self.levels,
            'bounds': list(self.bounds)
        }
    
@dataclass(eq=True, frozen=True)
class Time:
    name : str
    step : int
    @staticmethod
    def parse(src : str):
        tmp = src.strip().split(" ")
        return Time(name=tmp[0],step=int(tmp[-2]))
    def to_dict(self):
        return {
            'name': self.name,
            'step':self.step
        }
    
@dataclass
class Info:
    grids : List[Grid]
    verticals : List[Vertical]
    time : Time
    
    def to_dict(self):
        return {
            'grids': [grid.to_dict() for grid in self.grids],
            'verticals':[vertical.to_dict() for vertical in self.verticals],
            'time' : self.time.to_dict()
        }
    
    def get_grid(self,dimensions)->Grid:
        for grid in self.grids:
            if any(name in dimensions for name in (grid.axis[0].name,grid.axis[1].name)):
                return grid
        return None
    def get_vertical(self,dimensions)->Vertical:
        for vertical in self.verticals:
            if vertical.name in dimensions:
                return vertical
        return None
    def get_time(self,dimensions)->Time:
        if self.time.name in dimensions:
            return self.time
        return None
    @staticmethod
    def parseGrids(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while not src[cursor].startswith("Grid"):
            cursor += 1
        if cursor >= n:
            return []
        cursor += 1
        grids = []
        while grid := Grid.parse(src,cursor):
            grids.append(grid)
            cursor += 3
        return grids
    @staticmethod
    def parseVerticals(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while not src[cursor].startswith("Vertical"):
            cursor += 1
        if cursor >= n:
            return []
        cursor += 1
        verticals = []
        while vertical := Vertical.parse(src,cursor):
            verticals.append(vertical)
            cursor += 2
        return verticals
    
    @staticmethod       
    def parseTime(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while not src[cursor].startswith("Time"):
            cursor += 1
        if cursor >= n:
            return []
        cursor += 1
        return Time.parse(src[cursor])
    @staticmethod
    def parse(src : List[str]):
        grids = Info.parseGrids(src)
        verticals = Info.parseVerticals(src)
        time = Info.parseTime(src)
        return Info(grids=grids,verticals=verticals,time=time)

    

def test():
    src = ["Grid coordinates :",\
        "1 : lonlat                   : points=7008 (96x73)",\
        "longitude : -180 to 176.25 by 3.75 degrees_east  circular",\
        "latitude : -90 to 90 by 2.5 degrees_north",\
        "2 : lonlat                   : points=6912 (96x72)",\
        "longitude_1 : -178.125 to 178.125 by 3.75 degrees_east  circular",\
        "latitude_1 : -88.75 to 88.75 by 2.5 degrees_north",\
        "Vertical coordinates :",\
        "1 : generic                  : levels=19",\
        "depth : 10 to 4885 m",\
        "2 : generic                  : levels=1",\
        "unspecified : -1 unspecified",\
        "3 : generic                  : levels=20",\
        "depth_1 : 5 to 5192.65 m",\
        "Time coordinate :",\
        "t : 1 step",\
        "RefTime =  1850-12-00 00:00:00  Units = days  Calendar = 360_day",\
        "YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss",\
        "6750-06-01 00:00:00"]
    info = Info.parse(src)
    print(info)


if __name__ == "__main__":
    test()
    #print("Cannot execute in main")
    #import sys
    #sys.exit(1)