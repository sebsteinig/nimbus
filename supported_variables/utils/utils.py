from cdo import Cdo
import numpy as np
from typing import List,Union,Tuple
import os.path as path

def default_preprocessing(inputs:List[Tuple[str,str]],output_directory:str) -> List[Tuple[str,str]]:
    cdo = Cdo()
    outputs = []
    for input_file,var_name in inputs:
        selvar = cdo.selvar(var_name, input=input_file)
        name = path.basename(input_file).replace(".nc",".out.nc")
        out = path.join(output_directory,name)
        cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
        outputs.append((out,var_name))
    return outputs

def default_processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return inputs