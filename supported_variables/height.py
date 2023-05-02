if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import supported_variables.utils.utils as utils
from cdo import Cdo
import numpy as np
from typing import List, Tuple,Union
import os.path as path

@supported_variable
class Height:
    pass

@preprocessing(Height,'BRIDGE')
def preprocessing(inputs:List[Tuple[str,str]],output_directory:str) -> List[Tuple[str,str]]:
    cdo = Cdo()
    outputs = []
    
    orog,ht = inputs[0]
    omask,depthdepth = inputs[1]
    output = path.join(output_directory,"height.out.nc")

    selvar_orog = cdo.selvar(ht, input = orog)
    shifted_orog = cdo.sellonlatbox(-180,180,90,-90, input = selvar_orog)
    
    inputTmp = f"-invertlat -setmisstoc,0 -mulc,-1 -selvar,{depthdepth} {omask}"
    shifted_omask = cdo.sellonlatbox(-180,180,90,-90, input = inputTmp)
    
    cdo.add(input=f"{shifted_orog} {shifted_omask}", output = output)
    
    return [(output,None)]
    