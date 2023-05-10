import unittest
from utils.variables.pipelines.vertical_pipeline import *


class TestVerticalPipeLine(unittest.TestCase):
    
    def setUp(self) -> None:
        return super().setUp()
    
    def test_epsilons_success(self):
        vp = VerticalPipeline(desired_levels=[10,100,500,1000],desired_unit="hPa",vertical_name="",vertical_unit="mbar")
        e = vp.epsilons(vp.desired_levels)
        assert(e == {
            10 : [2.5,22.5],
            100 : [22.5,100],
            500 : [100,125],
            1000 : [125,250]
        })

    def test_select_indexes_success(self):
        vp = VerticalPipeline(desired_levels=[10,100,500,1000],desired_unit="hPa",vertical_name="",vertical_unit="mbar")
        distances = [
            {
                0 : 1,
                2 : 3,
                3 : 5, 
            },
            {
                4 : 10,
                5 : 9
            },
            {
                8 : 25,
                9 : 100
            },
            {
                10 : 0
            }
        ]
        
        indexes = vp.select_indexes(distances)
        assert(indexes == ",1,6,9,11")
        
        
    def test_eval_distances_success(self):
        vp = VerticalPipeline(desired_levels=[10,100,500,1000],desired_unit="hPa",vertical_name="",vertical_unit="mbar")
        levels = [12,40,114,300,590,800,1002]
        
        distances = vp.eval_distances(levels)
        assert(distances == [{0: 2}, {2: 14}, {4: 90}, {6: 2}])
        
    def test_convert_success(self):
        uc = UnitConverter.build("kPa","mbar")
        values = np.array([100.0,200.0,500.0,1000.0])
        converted = uc.convert(values)
        assert((converted == values*10).all)