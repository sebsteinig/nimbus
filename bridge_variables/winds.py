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
class Winds:
    realm = 'a'
    output_stream = "pc"
    look_for = "u_mm_p"

@bridge_preprocessing(Winds)
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    out = output.replace(".nc",".shifted.out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = input, output = out)
    return out
    
@bridge_processing(Winds)
def processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return utils.default_processing(inputs=inputs)
        