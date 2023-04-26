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
class Siconc:
    realm = 'o'
    output_stream = "pf"
    look_for = "iceconc_mm_uo"

@bridge_preprocessing(Siconc)
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    mask_file = inidata["qrparm"]["omask"]
    lsm_var_file = cdo.selvar("lsm", input = mask_file)

    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input}", options="-r -f nc")
    
    shifted = output.replace(".nc",".masked.shifted.out.nc")
    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
    
    return shifted
    
@bridge_processing(Siconc)
def processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return utils.default_processing(inputs=inputs)
        