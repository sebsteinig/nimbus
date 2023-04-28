if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import supported_variables.utils.utils as utils
from cdo import Cdo
import numpy as np
from typing import List,Union

@supported_variable
class Winds:
    realm = 'a'

@preprocessing(Winds,'BRIGDE')
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    out = output.replace(".nc",".shifted.out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = input, output = out)
    return out
    
