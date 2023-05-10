if __name__ == "__main__":
    from supported_variables.utils.supported_variable import (
        supported_variable,
        preprocessing,
    )
    import utils.utils as utils
else:
    from supported_variables.utils.supported_variable import (
        supported_variable,
        preprocessing,
    )
    import supported_variables.utils.utils as utils
from cdo import Cdo
from typing import List, Tuple, Union
import os.path as path


@supported_variable
class Sic:
    realm = "o"


@preprocessing(Sic, "BRIDGE")
def preprocessing(
    inputs: List[Tuple[str, str]], output_directory: str
) -> List[Tuple[str, str]]:
    cdo = Cdo()

    file, var = inputs[0]
    omask, lsm = inputs[1]

    name = path.basename(file).replace(".nc", ".out.nc")
    output = path.join(output_directory, name)

    omask = cdo.selvar(lsm, input=omask)

    mapped = cdo.ifnotthen(input=f"{omask} {file}", options="-r -f nc")

    mapped = cdo.selvar(var, input=mapped)
    cdo.sellonlatbox("-180,180,90,-90", input=mapped, output=output)

    return [(output, var)]
