import unittest
from utils.variables.info import *
from unit_tests.utils.mock_info import MockInfo

class TestInfo(unittest.TestCase):

    def test_parse_success(self):
        to_parse, len_grids, len_verticals = MockInfo.info_data()
        info = Info.parse(to_parse)
        self.assertEqual(len(info.grids), len_grids)
        self.assertEqual(len(info.verticals), len_verticals)
        to_parse2, len_grids2, len_verticals2 = MockInfo.info_2_data()
        info = Info.parse(to_parse2)
        self.assertEqual(len(info.grids), len_grids2)
        self.assertEqual(len(info.verticals), len_verticals2)

    def test_Axis_parse_failure(self):
        empty = Axis.parse("")
        self.assertIsNone(empty.name)
        self.assertIsNone(empty.bounds)
        self.assertIsNone(empty.step)
        self.assertIsNone(empty.direction)
        to_parse, name, bounds = MockInfo.incomplete_axis_data()
        incomplete_axis = Axis.parse(to_parse)
        self.assertEqual(incomplete_axis.name, name)
        self.assertEqual(incomplete_axis.bounds, bounds)
        self.assertIsNone(incomplete_axis.step)
        self.assertIsNone(incomplete_axis.direction)

    def test_Axis_parse_success(self):
        to_parse, name, bounds, step, direction = MockInfo.axis_data()
        axis = Axis.parse(to_parse)
        self.assertEqual(axis.name, name)
        self.assertEqual(axis.bounds, bounds)
        self.assertEqual(axis.step, step)
        self.assertEqual(axis.direction, direction)

    def test_Grid_parse_failure(self):
        self.assertIsNone(Grid.parse(["lala"], 0))
        self.assertEqual(Grid.parse(["2 : "], 0), Grid(category=None, points=None, axis=None))

    def test_Grid_parse_success(self):
        to_parse, category, points_num, x, y, ax1, ax2 = MockInfo.grid_data()
        grid = Grid.parse(to_parse, 0)
        self.assertEqual(grid.category, category)
        self.assertEqual(grid.points, (points_num, (x, y)))
        self.assertEqual(grid.axis, (ax1, ax2))

    def test_Vertical_parse_success(self):
        to_parse, category, name, levels, bounds, unit = MockInfo.vertical_data()
        vertical = Vertical.parse(to_parse, 0)
        self.assertEqual(vertical, Vertical(category=category, name=name,\
                                            levels=levels, bounds=bounds, unit=unit))
    
    def test_Time_parse_success(self):
        to_parse, name, step, format, ref, timestamp = MockInfo.time_data()
        time = Time.parse(to_parse[0], to_parse[1])
        self.assertEqual(time, Time(name, step, timestamp, ref, format))
        
    def test_get_vertical_failure(self):
        info = MockInfo.get_empty_info() 
        self.assertIsNone(info.get_vertical(('t', 'p', 'latitude', 'longitude')))
     
    def test_get_time_success(self):
        info = MockInfo.get_info()
        self.assertEqual(info.get_time(('t', 'p', 'latitude', 'longitude')), MockInfo.get_time())

    def test_get_grid_success(self):
        info = MockInfo.get_info()
        self.assertEqual(info.get_grid(('t', 'p', 'latitude', 'longitude')), MockInfo.get_grid())
