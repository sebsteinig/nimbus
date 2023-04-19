from typing import Dict
from variables.variable import *
from internship_netcdf2png import Environment
from cdo import Cdo

def tos_siconc(args:Dict,files:List[str]):
    cdo = Cdo()
    mask_file = args["env"].path_init(args["expId"],args["env"].inidata_file(args["expId"],("qrparm","omask")))
    lsm_var_file = cdo.selvar("lsm", input = mask_file)
    
    output_files = []
    for input in files :
        input_path,model = input
        #input_path = env.path_tmp_netcdf(expId,input_file)
        mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input_path}", options="-r -f nc")
        
        shifted_name = Environment.rename(*model,"masked","shifted","out")
        shifted = args["env"].path_tmp_netcdf(args["expId"],shifted_name)
        #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
        cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
        output_files.append(((shifted,shifted_name),))
    
    return output_files
def oceanCurrents(args:Dict,files:List[str]):
    cdo = Cdo()
    output_files = []
    for input in files :
        input_path,model = input
        #input_path = env.path_tmp_netcdf(expId,input_file)
        #TODO: check for missing token in the png converter
        #clean = cdo.setmisstoc(0, input = input_path, options = "-r")

        int_levels = "10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6"
        outTmp = cdo.setmisstoc(0, input = f" -intlevel,{int_levels} -selvar,W_ym_dpth {input_path}")
        
        remapnn_name = args["env"].rename(*model,"remapnn","masked","shifted","out")
        remapnn = args["env"].path_tmp_netcdf(args["expId"],remapnn_name)
        
        w_name = args["env"].rename(*model,"W","masked","shifted","out")
        wfile = args["env"].path_tmp_netcdf(args["expId"],w_name)
        
        cdo.sellonlatbox('-180,180,90,-90',input = input_path, output = remapnn)
        cdo.sellonlatbox('-180,180,90,-90',input = outTmp, output = wfile)
        
        output_files.append(((remapnn,remapnn_name),(wfile,w_name)))
    
    return output_files
def winds(args:Dict,files:List[str]):
    cdo = Cdo()
    output_files = []
    for input in files :
        input_path,model = input
        #input_path = env.path_tmp_netcdf(expId,input_file)
        name = args["env"].rename(*model,"shifted","out")
        out = args["env"].path_tmp_netcdf(args["expId"],name)
        cdo.sellonlatbox('-180,180,90,-90', input = input_path, output = out)
        output_files.append(((out,name),))
        
    return output_files
def liconc(args:Dict,files:List[str]):
    cdo = Cdo()
    output_files = []
    for input in files :
        input_path,model = input
        #input_path = env.path_tmp_netcdf(expId,input_file)
        sellevel = cdo.sellevel(9, input = input_path)
        selvar = cdo.selvar(args["selected_variable"], input=sellevel)
        name = args["env"].rename(*model,"out")
        out = args["env"].path_tmp_netcdf(args["expId"],name)
        cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
        output_files.append(((out,name),))
    return output_files

def default(args:Dict,files:List[str]):
    cdo = Cdo()
    output_files = []
    for input in files :
        if len(input) == 2:
            input_path,model = input
        else :
            input_path = input
            model = ["".join(input.split("/")[-1].split(".")[:-1])]
        #input_path = env.path_tmp_netcdf(expId,input_file)
        selvar = cdo.selvar(args["selected_variable"], input=input_path)
        name = args["env"].rename(*model,"out")
        out = args["env"].path_tmp_netcdf(args["expId"],name)
        cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
        output_files.append(((out,name),))
    return output_files

def builder()->Dict[str,Variable]:
    time = Dimension(name="time",stored_as="t")
    latitude = Dimension(name="latitude",stored_as={"latitude","latitude_1"})
    longitude = Dimension(name="longitude",stored_as="longitude")
    
    variables = {}
    
    variables["clt"] = Variable(name="clt",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("totCloud_mm_ua",)
    )
    variables["tas"] = Variable(name="tas",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("temp_mm_1_5m",)
    )
    variables["pr"] = Variable(name="pr",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("precip_mm_srf",)
    )
    variables["winds"] = Variable(name="winds",\
        dimensions=[time,latitude,longitude],\
        preprocess=winds,\
        stored_as=("u_mm_p",)
    )
    variables["snc"] = Variable(name="snc",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("snowCover_mm_srf",)
    )
    variables["liconc"] = Variable(name="liconc",\
        dimensions=[time,latitude,longitude],\
        preprocess=liconc,\
        stored_as=("fracPFTs_mm_srf",)
    )
    variables["pfts"] = Variable(name="pfts",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("fracPFTs_mm_srf",)
    )
    variables["tos"] = Variable(name="tos",\
        dimensions=[time,latitude,longitude],\
        preprocess=tos_siconc,\
        stored_as=("temp_mm_uo",)
    )
    variables["mlotst"] = Variable(name="mlotst",\
        dimensions=[time,latitude,longitude],\
        preprocess=default,\
        stored_as=("mixLyrDpth_mm_uo",)
    )
    variables["siconc"] = Variable(name="siconc",\
        dimensions=[time,latitude,longitude],\
        preprocess=tos_siconc,\
        stored_as=("iceconc_mm_uo",)
    )
    variables["oceanCurrents"] = Variable(name="oceanCurrents",\
        dimensions=[time,latitude,longitude],\
        preprocess=oceanCurrents,\
        stored_as=("ucurrTot_ym_dpth",)
    )
   
    return variables