import unittest
from utils.variables.pipelines.cleaning_pipeline import *

@dataclass
class LoggerProxy:
    flip = False
    def warning(self,*args):
        self.flip = True

class DatasetProxy:
    dimensions = {
        
    }
    
class VariableProxy:
    pass

class TestCleaningPipeLine(unittest.TestCase):
    
    def setUp(self) -> None:
        self.lon_correct = DataAxis(
            data = np.linspace(-180,180,num=96),
            size=96,
            index = 3
        )        
        self.lon_incorrect = DataAxis(
            data = np.linspace(180,-180,num=96),
            size=96,
            index = 2
        )
        
        self.lat_correct = DataAxis(
            data = np.linspace(90,-90,num=73),
            size=73,
            index = 2
        )        
        self.lat_incorrect = DataAxis(
            data = np.linspace(-90,90,num=73),
            size=73,
            index = 3
        )
        
        self.time_correct = DataAxis(
            data= None,
            index=1,
            size=12
        )
        self.time_incorrect = DataAxis(
            data= None,
            index=1,
            size=12
        )
        self.ver_correct = DataAxis(
            data= None,
            index=0,
            size=7
        )
        self.ver_incorrect = DataAxis(
            data= None,
            index=1,
            size=7
        )
        return super().setUp()
    
    def test_reorder_success(self):
        
        data = np.zeros((7,12,73,96))
        
        cp = CleaningPipeline(
            logger= LoggerProxy(),
            data=data,
            latitude=self.lat_correct,
            longitude=self.lon_correct,
            time=self.time_correct,
            vertical=self.ver_correct
        )
        
        reordered = cp.reorder(data)
        assert(reordered.shape == (7,12,73,96))
        
        cp = CleaningPipeline(
            logger= LoggerProxy(),
            data=data,
            latitude=self.lat_correct,
            longitude=self.lon_correct,
            time=self.time_incorrect,
            vertical=self.ver_incorrect
        )
        assert(reordered.shape == (7,12,73,96))
        
        cp = CleaningPipeline(
            logger= LoggerProxy(),
            data=data,
            latitude=self.lat_incorrect,
            longitude=self.lon_incorrect,
            time=self.time_incorrect,
            vertical=self.ver_incorrect
        )
        assert(reordered.shape == (7,12,73,96))
        
    def test_flip_success(self):      
        data = np.zeros((7,12,73,96))  
        logger = LoggerProxy()
        
        self.lat_correct.flip((-90,90),data,logger,False)
        assert(not logger.flip)       
        
        self.lat_incorrect.flip((-90,90),data,logger,False)
        assert(logger.flip)
        logger = LoggerProxy()        
        self.lon_correct.flip((-180,180),data,logger,True)
        assert(not logger.flip)       
        
        self.lon_incorrect.flip((-180,180),data,logger,True)
        assert(logger.flip)
        