from utils.metadata.metadata import *

class MockMetadata:
    var_s_1 : VariableSpecificMetadata
    var_s_2 : VariableSpecificMetadata
    var_s_3 : VariableSpecificMetadata = None
    var_g_1 : GeneralMetadata
    var_g_2 : GeneralMetadata
    var_g_3 : GeneralMetadata = None
    metadata : Metadata = Metadata()

    def __init__(self) -> None:
        self.var_s_1 = VariableSpecificMetadata.build(\
            original_variable_name = "name var1",\
               original_variable_long_name = "long name",\
               std_name = "std name 1",\
               model_name = "f",\
               min_max = [1, 2, 3]
                  )
        self.var_s_2 = VariableSpecificMetadata()
        self.var_g_1 = GeneralMetadata.build(\
            variable_name = "name g 1",\
            xsize = 1,\
            ysize = 2,\
            xfirst = 4.5,\
            timesteps = 4,\
            created_at = "12nv2014",\
            threshold = 5)
        self.var_g_2 = GeneralMetadata()
        