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
class Liconc:
    realm = 'a'

@preprocessing(Liconc,'BRIGDE')
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
    
        