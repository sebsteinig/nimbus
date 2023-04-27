from cdo import Cdo
import numpy as np
from typing import List,Union

def default_preprocessing(cdo:Cdo,
                          selected_variable:str,
                          input:str,output:str,
                          inidata) -> Union[str,List[str]]:
    
    selvar = cdo.selvar(selected_variable, input=input)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out

def default_processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return inputs