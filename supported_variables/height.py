if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import supported_variables.utils.utils as utils
from cdo import Cdo
import numpy as np
from typing import List,Union


@supported_variable
class Height:
    pass

@preprocessing(Height,'BRIGDE')
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
    