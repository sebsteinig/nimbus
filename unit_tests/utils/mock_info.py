from typing import List
from utils.variables.info import *
class MockInfo:
    
    @staticmethod
    def info_data():
        to_parse = ["Grid coordinates :",\
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
        return to_parse, 2, 3

    @staticmethod
    def info_2_data():
        to_parse = [
        'Grid coordinates :',\
        '1 : lonlat                   : points=41184 (288x143)',\
        'longitude_2 : -179.375 to 179.375 by 1.25 degrees_east  circular',\
        'latitude_1 : -88.75 to 88.75 by 1.25 degrees_north',\
        'Vertical coordinates :',\
        '1 : generic                  : levels=20',\
        'depth_1 : 5 to 5192.45 m',\
        'Time coordinate :',\
        't : 1 step',\
        'RefTime =  2449-09-01 00:00:00  Units = days  Calendar = 360_day',\
        'YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss',\
         '2670-06-01 00:00:00']
        return to_parse, 1, 1
        
    @staticmethod
    def grid_data():
        category = "lonlat"
        points_num = 6912
        x = 96
        y = 72
        ax = Axis(name=None, bounds=None, step=None, direction=None)
        to_parse = [f"2 : {category}                   : points={points_num} ({x}x{y})",\
            "",\
            ""  ]
        return to_parse, category, points_num, x, y, ax, ax

    @staticmethod
    def incomplete_axis_data():
        name = "lon"
        bounds = (1, 2)
        return f"{name} : {bounds[0]} to {bounds[1]}", name, bounds

    @staticmethod
    def axis_data():
        name = "longitude"
        bounds = (-180, 176.25)
        step = 3.75
        direction = "degrees_east"
        to_parse = f"{name} : {bounds[0]} to {bounds[1]} by {step} {direction}  circular"
        return to_parse, name, bounds, step, direction
    
    @staticmethod
    def vertical_data():
        category = "generic"
        name = "depth"
        levels = 19
        bounds = (10, 4885)
        unit = "m"
        return [f"1 : {category}                  : levels={levels}",\
        f"{name} : {bounds[0]} to {bounds[1]} {unit}"], category, name, levels, bounds, unit

    @staticmethod
    def time_data():
        name = "t"
        step = 1
        format = "YYYY-MM-DD hh:mm:ss"
        ref = "2449-09-01 00:00:00"
        timestamp = ["2670-06-01 00:00:00"]
        to_parse = (f'{name} : {step} step',[f'RefTime =  {ref}  Units = days  Calendar = 360_day',\
        f'{format}  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss  YYYY-MM-DD hh:mm:ss',\
         f'{timestamp[0]}'])
        return to_parse, name, step, format, ref, timestamp
        
    @staticmethod
    def get_empty_info():
        return Info(grids=[Grid(None, None, None)], verticals=[], time=None)
    
    @staticmethod
    def get_info():
        return Info(
            grids = [MockInfo.get_grid()],
            verticals = [Vertical(category = "generic", name = "depth",\
                        levels = 19, bounds = (10, 4885), unit = "m"),
                        Vertical(category = "generic", name = "depth_1",\
                        levels = 20, bounds = (10, 4885), unit = "m")],
            time = MockInfo.get_time()
        )
    
    @staticmethod
    def get_time():
        return Time(name = "t", step = 1, timestamps = ["2670-06-01 00:00:00"],\
                    ref = "2449-09-01 00:00:00", format = "YYYY-MM-DD hh:mm:ss")
    
    @staticmethod
    def get_grid():
        return Grid(category = "lonlat", points = (6912, (96,72)), axis=
                    (Axis(name = "longitude",  bounds = (-180, 176.25),
                        step = 3.75, direction = "degrees_east"),
                    Axis(name = "latitude",  bounds = (-90, 90),
                        step = 3.75, direction = "degrees_north")))
