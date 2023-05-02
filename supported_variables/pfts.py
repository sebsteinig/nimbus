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


    