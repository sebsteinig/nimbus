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
class Pfts:
    realm = 'a'
    output_stream = "pt"
    look_for = "fracPFTs_mm_srf"

@bridge_preprocessing(Pfts)
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    return utils.default_preprocessing(cdo=cdo,\
        selected_variable=selected_variable,\
        input=input,\
        output=output,\
        inidata=inidata)
    
@bridge_processing(Pfts)
def processing(inputs:List[np.ndarray]) -> List[np.ndarray]:
    return utils.default_processing(inputs=inputs)
        