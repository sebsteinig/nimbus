if __name__ == "__main__":
    from bridge_variables.utils.bridge_variable import bridge_variable,bridge_preprocessing,bridge_processing
    import utils.utils as utils
else :
    from bridge_variables.utils.bridge_variable import bridge_variable,bridge_preprocessing,bridge_processing
    import bridge_variables.utils.utils as utils
from cdo import Cdo
import numpy as np
from typing import List,Union

@bridge_variable
class Height:
    inidata = "qrparm.orog"

@bridge_preprocessing(Height)
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:
    selvar_orog = cdo.selvar("ht", input = inidata["qrparm"]["orog"])
    
    shifted_orog = cdo.sellonlatbox(-180,180,90,-90, input = selvar_orog)
    
    inputTmp = f"-invertlat -setmisstoc,0 -mulc,-1 -selvar,depthdepth {inidata['qrparm']['omask']}"
    shifted_omask = cdo.sellonlatbox(-180,180,90,-90, input = inputTmp)
    
    tmp_name = output.split("/")[-1]
    
    output = output.replace(tmp_name,"/height.out.nc")
    cdo.add(input=f"{shifted_orog} {shifted_omask}", output = output)
    
    return output
    
@bridge_processing(Height)
def processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return utils.default_processing(inputs=inputs)
        