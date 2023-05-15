if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing,processing
    import supported_variables.utils.utils as utils
from utils.import_cdo import cdo
import numpy as np
from typing import List,Union,Tuple
import os.path as path

@supported_variable
class Liconc:
    realm = 'a'


@preprocessing(Liconc,'BRIDGE')
def preprocessing(inputs:List[Tuple[str,str]],output_directory:str) -> List[Tuple[str,str]]:
    outputs = []
    for input_file,var_name in inputs:
        name = path.basename(input_file).replace(".nc",".out.nc")
        out = path.join(output_directory,name)
        cdo.sellonlatbox('-180,180,90,-90', input = f"-selvar,{var_name} -sellevel,9 {input_file}", output = out)
        outputs.append((out,var_name))
    return outputs