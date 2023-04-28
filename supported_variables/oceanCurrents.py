if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import supported_variables.utils.utils as utils
from cdo import Cdo
from typing import List,Union

@supported_variable
class OceanCurrents:
    realm = 'o'

@preprocessing(OceanCurrents,'BRIGDE')
def preprocessing(cdo:Cdo,\
    selected_variable:str,\
    input:str,\
    output:str,\
    inidata) -> Union[str,List[str]]:

    #TODO: check for missing token in the png converter
    #clean = cdo.setmisstoc(0, input = input_path, options = "-r")

    int_levels = "10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6"
    
    #inputW = cdo.setmisstoc(0, input = f" -intlevel,{int_levels} -selvar,W_ym_dpth {input}")
    inputRemapnn = input#cdo.selvar("ucurrTot_ym_dpth", input=input)
    
    remapnn = output.replace(".nc",".remapnn.masked.shifted.out.nc")
    #wfile = output.replace(".nc",".W.masked.shifted.out.nc")
    
    cdo.sellonlatbox('-180,180,90,-90',input = inputRemapnn, output = remapnn)
    #cdo.sellonlatbox('-180,180,90,-90',input = inputW, output = wfile)       
    return remapnn

        