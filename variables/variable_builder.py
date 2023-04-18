from typing import Dict
from variables.variable import *
from internship_netcdf2png import Environment
from cdo import Cdo

def tos_siconc(cdo:Cdo,selected_variable:str,input:str,output:str,extra:dict):
    mask_file = extra["inidata"]("qrparm","omask")
    lsm_var_file = cdo.selvar("lsm", input = mask_file)

    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input}", options="-r -f nc")
    
    shifted = output.replace(".nc",".masked.shifted.out.nc")
    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
    
    return shifted

def oceanCurrents(cdo:Cdo,selected_variable:str,input:str,output:str,extra:dict):
    #TODO: check for missing token in the png converter
    #clean = cdo.setmisstoc(0, input = input_path, options = "-r")

    int_levels = "10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6"
    outTmp = cdo.setmisstoc(0, input = f" -intlevel,{int_levels} -selvar,W_ym_dpth {input}")

    remapnn = output.replace(".nc",".remapnn.masked.shifted.out.nc")
    
    wfile = output.replace(".nc",".W.masked.shifted.out.nc")
    
    cdo.sellonlatbox('-180,180,90,-90',input = input, output = remapnn)
    cdo.sellonlatbox('-180,180,90,-90',input = outTmp, output = wfile)       
    return [remapnn,wfile]

def winds(cdo:Cdo,selected_variable:str,input:str,output:str,extra:dict):
    out = output.replace(".nc",".shifted.out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = input, output = out)
    return out

def liconc(cdo:Cdo,selected_variable:str,input:str,output:str,extra:dict):
    sellevel = cdo.sellevel(9, input = input)
    selvar = cdo.selvar(selected_variable, input=sellevel)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out

def default(cdo:Cdo,selected_variable:str,input:str,output:str,extra:dict):
    selvar = cdo.selvar(selected_variable, input=input)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out
    
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