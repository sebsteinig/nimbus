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

from dataclasses import dataclass, field
from typing import List,Union,Set,Callable,Tuple,Dict,Type

""" class Axis """
@dataclass(eq=True)
class Axis:
    name   : str = None
    bounds : Tuple[float,float] = (None, None)
    step   : float = None
    direction : str = None
    
    """
        parse axis. example of inputs :
            "longitude : -180 to 176.25 by 3.75 degrees_east  circular"
            "latitude : -90 to 90 by 2.5 degrees_north"
        example of output :
            Axis(name = latitude, bounds = (-90, 90), step = 2.5, direction = degrees_north)
        param :
            src : str (string that contains info about axis)
        return :
            Axis 
    """
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
                step = float(tokens[cursor+1])
                direction = tokens[cursor+2]

        return Axis(bounds=bounds, direction=direction, name=name, step=step)

""" class Grid """  
@dataclass(eq=True)
class Grid:
    category : str = None
    points   : Tuple[int,Tuple[int,int]] = (None, (None, None))
    axis : Tuple[Axis,Axis] = (None, None)

    """
        parser for Grid
        example of input : 
            "1 : lonlat                   : points=7008 (96x73)"
            {input parse Axis}
        param :
            src : List[str]
            cursor : int
        return :
            Grid
    """
    @staticmethod
    def parse(src : List[str],cursor:int):
        header_tokens = src[cursor].strip().split(" ")
        header_tokens = [ h for h in header_tokens if h != ""]
        if (len(header_tokens) < 2 or not header_tokens[0].isdigit())\
            or header_tokens[1] != ":":
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
                shape = (int(shape[0]),int(shape[1]))
            else :
                shape = None
        points = (size,shape)
            
        axis = (Axis.parse(src[cursor+1]),Axis.parse(src[cursor+2]))
        return Grid(category=category,axis=axis,points=points)

@dataclass(eq=True, frozen=True)
class Vertical:
    category : str = None
    name     : str = None
    levels   : int = None
    bounds   : Tuple[float,float] = (None, None)
    unit : str = None

    """
        parse info for Vertical
        param :
            src : List[str]
            cursor : int
        return :
            Vertical
    """
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
            if "by" not in vertical_tokens[to_index:] and "level" not in vertical_tokens[to_index:]:
                unit = vertical_tokens[to_index + 2]
            else :
                unit = None
        else :
            bounds = None
            unit = None
        return Vertical(category=category,name=name,levels=levels,bounds=bounds,unit=unit)
    
""" class Time """
@dataclass(eq=True, frozen=True)
class Time:
    name : str = None
    step : int = None
    timestamps : list = field(default_factory=lambda:[])
    ref : str = None
    format: str = None

    """
        parse info for time.
        param :
            src : str
            dates : str
        return :
            Time
    """
    @staticmethod
    def parse(src : str, dates : List[str] = []):
        tmp = src.strip().split(" ")
        timestamps = []
        if len(dates) >= 2 :
            tmp2 = dates[0].strip().split("  ")[1] if len(dates[0].strip().split("  "))> 1 else None
            format = dates[1].strip().split("  ")[0] if len(dates[1].strip().split("  "))>0 else None
            for group in dates[2::]:
                group_list = group.strip().split("  ")
                for date in group_list:
                    timestamps.append(date)
            return Time(name=tmp[0],step=int(tmp[-2]), timestamps= timestamps, ref = tmp2, format= format)
        return Time(name=tmp[0],step=int(tmp[-2]), timestamps= timestamps, ref =None, format= None)
    
""" class Info """
@dataclass
class Info:
    grids : List[Grid]
    verticals : List[Vertical]
    time : Time
    
    """
        returns a dict containing the needed values in the metadata.
        param :
            None
        return :
            dict
    """
    def to_metadata(self):
        res = {}
        grid = self.grids[0]
        vertical = self.verticals[0]
        res['xsize'] = grid.points[1][0]
        res['ysize'] = grid.points[1][1]
        res['levels'] = 1 if vertical is None else vertical.levels
        res['timesteps'] =  1 if self.time is None else self.time.step
        res['xfirst'] = grid.axis[0].bounds[0]
        res['xinc'] = grid.axis[0].step
        res['yfirst'] = grid.axis[1].bounds[0]
        res['yinc'] = grid.axis[1].step
        res['timestamps'] = self.time.timestamps
        return res
        
    """
        retrieve info with one grid and one vertical for specific dimensions.
        param :
            dimensions : List[str]
        return :
            Info
    """
    def reduce(self,dimensions) -> 'Info':
        grid = self.get_grid(dimensions)
        vertical = self.get_vertical(dimensions)
        
        return Info(grids=[grid],verticals=[vertical],time=self.time)
    
    """
        retrieve the grid given dimensions
        param :
            dimensions : List[str]         
        return :
            Grid
    """
    def get_grid(self,dimensions)->Grid:
        for grid in self.grids:
            if any(name in dimensions for name in (grid.axis[0].name,grid.axis[1].name)):
                return grid
        return None

    """
        retrieve the vertical given dimensions
        param :
            dimensions : List[str]
        return :
            Vertical
    """
    def get_vertical(self,dimensions)->Vertical:
        for vertical in self.verticals:
            if vertical.name in dimensions:
                return vertical
        return None

    """
        retrieve the time given dimensions
        param :
            dimensions : List[str]
        return :
            Time
    """
    def get_time(self,dimensions)->Time:
        if self.time is not None and self.time.name in dimensions:
            return self.time
        return None

    """
        calls the parse from the Grid class
        param :
            src : List[str]
        return :
            List[Grid]
    """
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

    """
        calls the parse from the Vertical class
        param :
            src : List[str]
        return :
            List[Vertical]
    """    
    @staticmethod
    def parseVerticals(src : List[str]) -> List[Vertical]:
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
    
    """
        calls the parse from the Time class
        param :
            src : List[str]
        return :
            None
    """
    @staticmethod       
    def parseTime(src : List[str]) -> Time:
        n = len(src)
        cursor = 0
        while  cursor < n and not src[cursor].startswith("Time"):
            cursor += 1
        if cursor >= n:
            return None
        cursor += 1
        if src[cursor+1].startswith("RefTime") :
            return Time.parse(src[cursor], src[cursor+1:n])
        return Time.parse(src[cursor])
    
    """
        main parse function that calls the others
        param :
            src : List[str]
        return :
            Info
    """
    @staticmethod
    def parse(src : List[str]):
        grids = Info.parseGrids(src)
        verticals = Info.parseVerticals(src)
        time = Info.parseTime(src)
        return Info(grids=grids,verticals=verticals,time=time)


if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)