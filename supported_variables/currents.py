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
from utils.import_cdo import cdo
from typing import List, Union, Tuple
import os.path as path


@supported_variable
class Currents:
    realm = "o"


@preprocessing(Currents, "BRIDGE")
def preprocessing(
    inputs: List[Tuple[str, str]], output_directory: str
) -> List[Tuple[str, str]]:
    outputs = []

    u_file, u_var = inputs[0]
    v_file, v_var = inputs[1]

    name = path.basename(u_file).replace(".nc", ".u.out.nc")
    out = path.join(output_directory, name)
    cdo.sellonlatbox("-180,180,90,-90", input = f"-selvar,{u_var} {u_file}", output=out)
    outputs.append((out, u_var))

    name = path.basename(v_file).replace(".nc", ".v.out.nc")
    out = path.join(output_directory, name)
    cdo.sellonlatbox("-180,180,90,-90", input = f"-selvar,{v_var} {v_file}", output=out)
    outputs.append((out, v_var))

    return outputs
