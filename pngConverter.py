from pngConverter_old import *
class TooManyVariables(Exception):pass
class TooManyInputs(Exception):pass

def save(output : np.ndarray, output_file : str, mode = 'L'):
    out = np.squeeze(output)
    img_ym = Image.fromarray(np.uint8(out), mode)
    img_ym.save(output_file + ".png")

def eval_shape(size:int) -> Tuple(bool, bool, dict):
    res = {}
    levelExists = False
    timeExists = False
    match size:
        case 4:
            res["level"] = np.shape(input[0])[0]
            res["time"] = np.shape(input[0])[1]
            levelExists = True
            timeExists = True
            start = 2 
        case 3 :
            res["time"] = np.shape(input[0])[0]
            timeExists = True
            start = 1
        case 2:
            start = 0
        case _ :
            raise TooManyVariables(f"{size} > 4 : there are too many variables")
    res["latitude"] = np.shape(input[0])[start]
    res["longitude"] = np.shape(input[0])[start + 1]  
    return timeExists, levelExists, res

def eval_input(size:int) -> Tuple(int, str):
    match size:
        case 1 :
            dim = 1
            mode = 'L'
        case 2|3:
            dim = 3
            mode = 'RGB'
        case 4 :
            dim = 4
            mode = "RGBA"
        case _:
            raise TooManyInputs(f"{size} > 4 : there are too many inputs")
    return dim, mode
            
def shape_output(shapes:dict, timeExists:bool, levelExists:bool, dim:int) -> np.ndarray :
    if timeExists :
        output = np.zeros( ( shapes["latitude"] * shapes["level"], shapes["longitude"] * shapes["time"], dim) )\
            if levelExists else np.zeros( ( shapes["latitude"], shapes["longitude"] * shapes["time"], dim) )
    else :        
        output = np.zeros( ( shapes["latitude"] * shapes["level"], shapes["longitude"], dim) )\
            if levelExists else np.zeros( ( shapes["latitude"], shapes["longitude"], dim) )
    return output
        


def iterate_in_time(time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for index in range(time):
            if(len(input) == 1) :
                output[:,index* longitude  : ((index+1)* longitude)] = \
                np.linalg.norm(input[0][index,:,:]) * 255
            if numVar == 2 and len(input) == 2:
                output[:,index* longitude  : ((index+1)* longitude), numVar ] = \
                    np.zeros((latitude, longitude))
            else :
                output[:,index* longitude : ((index+1)* longitude, numVar )] = \
                np.linalg.norm(input[numVar][index,:,:]) * 255 
    return output

def iterate_in_time_and_level(level:int, time:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for lev in range(level):
        for index in range(time):
            if(len(input) == 1) :
                output[lev*latitude : (lev+1)*latitude, index* longitude  : ((index+1)* longitude)] = \
                np.linalg.norm(input[0][lev,index,:,:]) * 255
            if numVar == 2 and len(input) == 2:
                output[lev*latitude : (lev+1)*latitude,index* longitude  : ((index+1)* longitude), numVar ] = \
                    np.zeros((latitude, longitude))
            else :
                output[lev*latitude : (lev+1)*latitude,index* longitude : ((index+1)* longitude, numVar )] = \
                np.linalg.norm(input[numVar][lev, index,:,:]) * 255 
    return output

def iterate_in_level(level:int, longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    for lev in range(level):
            if(len(input) == 1) :
                output[lev*latitude : (lev+1)*latitude, :] = \
                np.linalg.norm(input[0][lev,:,:]) * 255
            if numVar == 2 and len(input) == 2:
                output[lev*latitude : (lev+1)*latitude,:, numVar] = \
                    np.zeros((latitude, longitude))
            else :
                output[lev*latitude : (lev+1)*latitude,:, numVar] = \
                np.linalg.norm(input[numVar][lev,:,:]) * 255 
    return output

def iterate_in_space_only (longitude:int, latitude:int, numVar:int, input:list, output:np.ndarray) -> np.ndarray:
    if(len(input) == 1) :
        output= np.linalg.norm(input[0]) * 255
    if numVar == 2 and len(input) == 2:
        output[:,:, numVar] = np.zeros((latitude, longitude))
    else :
        output[:,:, numVar] = np.linalg.norm(input[numVar]) * 255 
    return output




def convert(input:list, output_filename:str) -> str:
    dim, mode = eval_input(len(input))
    timeExists, levelExists, shapes = eval_shape(len (np.shape(input[0])))
    output = shape_output(shapes, timeExists, levelExists, dim)
    for numVar in range(dim) :
        if timeExists:
            if levelExists :
                output = iterate_in_time_and_level(shapes["level"], shapes["time"], shapes["longitude"], shapes["latitude"], numVar, input, output)
            else :
                output = iterate_in_time(shapes["time"], shapes["longitude"], shapes["latitude"], numVar, input, output)
        else:
            if levelExists:
                output = iterate_in_level(shapes["level"], shapes["longitude"], shapes["latitude"], numVar, input, output)
            else:
                output = iterate_in_space_only(shapes["longitude"], shapes["latitude"], numVar, input, output)
    save(output, output_filename, mode)
    return output_filename

    








    
def test(input_file,expId,variable_name,output_variable,output_dir) :
    with Dataset(input_file,"r",format="NETCDF4") as dataset:
        print(f"converting {input_file}")
        env = Environment(dataset)
        input = env.get(variable_name)
        assert_input(input,env)
        if not output_variable in OutputVariable._value2member_map_:
            raise OutputVariableNotRecognized(f"{output_variable} is not valid output variable")
        out_meta = env.outputMeta[OutputVariable(output_variable)]
        preprocess(input,env,out_meta,None)
        
        mean = np.nanmean(input.data, axis=env.rank(input,Dimension.Time))
        mean = norm(mean, out_meta.bound[0],  out_meta.bound[1]) * 255
        mean = clean(mean)
        input.data = np.squeeze(input.data)
        convert(input, env, out_meta, "o.pf.test")

if __name__ == "__main__":
    input_file = "texpa1o.pf.clim.masked.shifted.nc"
    expId = "texpa1"
    variable_name = "temp_mm_uo"
    output_variable = "tos"
    test(input_file,expId,variable_name,output_variable,"./")