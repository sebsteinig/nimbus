if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable,preprocessing
    import supported_variables.utils.utils as utils
from cdo import Cdo
from typing import List,Union

@supported_variable
class Pfts:
    realm = 'a'

@preprocessing(Pfts,'BRIGDE')
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
    