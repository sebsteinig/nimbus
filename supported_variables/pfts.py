if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,processing,preprocessing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,processing,preprocessing
    import supported_variables.utils.utils as utils
from utils.import_cdo import cdo
from typing import Any, List,Union,Tuple
import numpy as np
import os.path as path

@supported_variable
class Pfts:
    realm = 'a'


@preprocessing(Pfts,'BRIDGE')
def preprocessing(inputs:List[Tuple[str,str]],output_directory:str) -> List[Tuple[str,str]]:
    
    file,var_name = inputs[0]
    name_levels_1 = path.basename(file).replace(".nc","l1.out.nc")
    out_levels_1 = path.join(output_directory,name_levels_1)
    name_levels_2 = path.basename(file).replace(".nc","l2.out.nc")
    out_levels_2 = path.join(output_directory,name_levels_2)
    
    selvar = cdo.selvar(var_name, input=file)
    
    
    out_1 = cdo.sellevidx("1,2,5",input = selvar)
    cdo.sellonlatbox('-180,180,90,-90', input = out_1, output = out_levels_1)
    
    out_2 = cdo.sellevidx("8,9",input = selvar)
    add_3 = cdo.sellevidx("3",input = selvar)
    add_4 = cdo.sellevidx("4",input = selvar)
    add = cdo.add(input=f"{add_3} {add_4}")
    
    out_2 = cdo.merge(input=f"{out_2} {add}")
    
    cdo.sellonlatbox('-180,180,90,-90', input = out_2, output = out_levels_2)

    return [(out_levels_1,var_name),(out_levels_2,var_name)]

@processing(Pfts,'BRIDGE')
def process(inputs:Tuple[List[Tuple[np.ndarray,Any]],str]) -> List[Tuple[List[np.ndarray],str]]:
    array,filename = inputs
    
    first = []
    levels,metadata = array[0]
    for level in levels:
        first.append((level,metadata))

    second = []
    levels,metadata = array[1]
    for level in levels:
        second.append((level,metadata))
    
    return [(first,filename+".1.of.2"),(second,filename+".2.of.2")]