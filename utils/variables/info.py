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
        if src is None or src == "":
            return Axis(name=None,bounds=None,step=None,direction=None)
        tokens = src.strip().split(" ")
        tokens = [ h for h in tokens if h != ""]
        
        cursor = 0
        name = tokens[cursor]
        step = None
        direction = None
        if len(tokens) <= 1 or tokens[cursor+1] != ":":
            return Axis(name=name,bounds=None,step=None,direction=None)
        cursor += 2 # eat ':' 
        n = len(tokens)
        if cursor + 3 <= n and "to" in tokens[cursor:cursor+3]:
            bounds = (float(tokens[cursor]),float(tokens[cursor+2]))
        else :
            bounds = None
        if "by" in tokens:
            cursor = tokens.index("by")
            if cursor + 2 < n:
                step = tokens[cursor+1]
                direction = tokens[cursor+2]

        return Axis(bounds=bounds, direction=direction, name=name, step=step)
        
    def to_dict(self):
        return {
            'name' : self.name,
            'bounds':  [] if self.bounds is None else list(self.bounds),
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
        header_tokens = src[cursor].strip().split(" ")
        header_tokens = [ h for h in header_tokens if h != ""]
        if not header_tokens[0].isdigit():
            return None
        h_cursor = 2 # eat ':'
        n = len(header_tokens)
        if h_cursor >= n :
            return Grid(category=None,points=None,axis=None)
        category = header_tokens[h_cursor]
        h_cursor += 2 # eat ':'
        if h_cursor + 1 < n:
            if "points" in header_tokens[h_cursor] :
                size = int(header_tokens[h_cursor].split("=")[-1])
            else :
                size = None
            if "x" in header_tokens[h_cursor + 1] :
                shape = tuple(header_tokens[h_cursor + 1][1:-1].split("x"))
            else :
                shape = None
        points = (size,shape)
            
        axis = (Axis.parse(src[cursor+1]),Axis.parse(src[cursor+2]))
        return Grid(category=category,axis=axis,points=points)

    def to_dict(self):
        return {
            'category' : self.category,
            'points': [self.points[0],[self.points[1][0],self.points[1][1]]],
            'axis' : [self.axis[0].to_dict(), self.axis[1].to_dict()]
        }

@dataclass(eq=True, frozen=True)
class Vertical:
    category : str
    name     : str
    levels   : int
    bounds   : Tuple[float,float]
    unit : str

    @staticmethod
    def parse(src : List[str],cursor:int):
        if cursor >= len(src):
            return None
        header_tokens = src[cursor].strip().split(" ")
        header_tokens = [ h for h in header_tokens if h != ""]
        
        if not header_tokens[0].isdigit():
            return None
        h_cursor = 2 # eat ':'
        n = len(header_tokens)
        if h_cursor >= n :
            return Vertical(category=None,levels=None,bounds=None,name=None,unit=None)
        
        category = header_tokens[h_cursor]
        h_cursor += 2 # eat ':'
        levels = None
        if h_cursor < n and "levels" in header_tokens[h_cursor]:
            levels = int(header_tokens[h_cursor].split("=")[-1])

        n = len(src)
        if cursor + 1 >= n :
            return Vertical(category=category,levels=levels,bounds=None,name=None,unit=None)
        vertical = src[cursor+1]
        vertical_tokens = vertical.strip().split(" ")
        name = vertical_tokens[0]
        v_cursor = 2 # eat ':'
        if "to" in vertical_tokens[v_cursor:]:
            to_index = vertical_tokens.index("to")
            bounds = (float(vertical_tokens[to_index - 1]),float(vertical_tokens[to_index + 1]))
            
            if "by" not in vertical_tokens[to_index:]:
                unit = vertical_tokens[to_index + 2]
            else :
                unit = None
        else :
            bounds = None
            unit = None
        return Vertical(category=category,name=name,levels=levels,bounds=bounds,unit=unit)
    
    def to_dict(self):
        return {
            'category' : self.category,
            'name': self.name,
            'levels':self.levels,
            'bounds': [] if self.bounds is None else list(self.bounds),
            'unit':self.unit
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
        if self.time is not None and self.time.name in dimensions:
            return self.time
        return None
    @staticmethod
    def parseGrids(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while  cursor < n and  not src[cursor].startswith("Grid"):
            cursor += 1
        if cursor >= n:
            return []
        cursor += 1
        grids = []
        grid = Grid.parse(src,cursor)
        while grid is not None:
            grids.append(grid)
            cursor += 3
            grid = Grid.parse(src,cursor)
        return grids
    @staticmethod
    def parseVerticals(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while cursor < n and not src[cursor].startswith("Vertical"):
            cursor += 1
        if cursor >= n:
            return []
        cursor += 1
        verticals = []
        vertical = Vertical.parse(src,cursor)
        while vertical is not None:
            verticals.append(vertical)
            cursor += 2
            vertical = Vertical.parse(src,cursor)
        return verticals
    
    @staticmethod       
    def parseTime(src : List[str]) -> List[Grid]:
        n = len(src)
        cursor = 0
        while  cursor < n and not src[cursor].startswith("Time"):
            cursor += 1
        if cursor >= n:
            return None
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