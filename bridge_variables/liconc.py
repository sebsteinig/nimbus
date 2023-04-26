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
class Liconc:
    realm = 'a'
    output_stream = "pt"
    look_for = "fracPFTs_mm_srf"

@bridge_preprocessing(Liconc)
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    sellevel = cdo.sellevel(9, input = input)
    selvar = cdo.selvar(selected_variable, input=sellevel)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out
    
@bridge_processing(Liconc)
def processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return utils.default_processing(inputs=inputs)
        