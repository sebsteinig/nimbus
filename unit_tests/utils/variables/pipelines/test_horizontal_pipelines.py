import unittest
from utils.variables.pipelines.horizontal_pipeline import *
from utils.variables.info import Axis,Grid


class TestHorizontalPipeLine(unittest.TestCase):
    
    def setUp(self) -> None:
        self.grid = Grid(points=(180*180,(180,180)),axis=(
            Axis(name='',bounds=(-180,180),step=2,direction=''),
            Axis(name='',bounds=(90,-90),step=1,direction='')
        ),category='lonlat')
        self.resolution = (4,2)
        return super().setUp()
    
    def test_compute_success(self):
        hp = HorizontalPipeline(self.resolution,self.grid)
        grid = hp.compute()
    
        assert(grid.points[1][0] == 90)
        assert(grid.points[1][1] == 90)
        
        assert(abs(grid.axis[0].bounds[0] + (grid.points[1][0]-1)*grid.axis[0].step) <= self.grid.axis[0].bounds[1])