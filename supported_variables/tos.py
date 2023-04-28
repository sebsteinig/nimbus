if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import supported_variables.utils.utils as utils
from cdo import Cdo
from typing import List,Union

@supported_variable
class Tos:
    realm = 'o'

@preprocessing(Tos,'BRIGDE')
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
    
        