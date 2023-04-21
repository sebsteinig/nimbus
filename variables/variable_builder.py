from typing import Dict
from variables.variable import *
from cdo import Cdo

def tos_siconc(cdo:Cdo,selected_variable:str,input:str,output:str,inidata):
    mask_file = inidata["qrparm"]["omask"]
    lsm_var_file = cdo.selvar("lsm", input = mask_file)

    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input}", options="-r -f nc")
    
    shifted = output.replace(".nc",".masked.shifted.out.nc")
    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
    
    return shifted
def height(cdo:Cdo,selected_variable:str,input:str,output:str,inidata):
    mask_file = inidata["qrparm"]["omask"]
    lsm_var_file = cdo.selvar("lsm", input = mask_file)

    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input}", options="-r -f nc")
    
    shifted = output.replace(".nc",".masked.shifted.out.nc")
    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
    
    return shifted

def oceanCurrents(cdo:Cdo,selected_variable:str,input:str,output:str,inidata):
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

def winds(cdo:Cdo,selected_variable:str,input:str,output:str,inidata):
    out = output.replace(".nc",".shifted.out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = input, output = out)
    return out

def liconc(cdo:Cdo,selected_variable:str,input:str,output:str,file_manager):
    sellevel = cdo.sellevel(9, input = input)
    selvar = cdo.selvar(selected_variable, input=sellevel)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out

def default(cdo:Cdo,selected_variable:str,input:str,output:str,inidata):
    selvar = cdo.selvar(selected_variable, input=input)
    out = output.replace(".nc",".out.nc")
    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
    return out
    
def builder()->Dict[str,Variable]:
    variables = {}
    
    variables["clt"] = Variable(name="clt",\
        preprocess=default,\
        look_for=("totCloud_mm_ua",)
    )
    variables["tas"] = Variable(name="tas",\
        preprocess=default,\
        look_for=("temp_mm_1_5m",)
    )
    variables["pr"] = Variable(name="pr",\
        preprocess=default,\
        look_for=("precip_mm_srf",)
    )
    variables["winds"] = Variable(name="winds",\
        preprocess=winds,\
        look_for=("u_mm_p",)
    )
    variables["snc"] = Variable(name="snc",\
        preprocess=default,\
        look_for=("snowCover_mm_srf",)
    )
    variables["liconc"] = Variable(name="liconc",\
        preprocess=liconc,\
        look_for=("fracPFTs_mm_srf",)
    )
    variables["pfts"] = Variable(name="pfts",\
        preprocess=default,\
        look_for=("fracPFTs_mm_srf",)
    )
    variables["tos"] = Variable(name="tos",\
        preprocess=tos_siconc,\
        look_for=("temp_mm_uo",)
    )
    variables["mlotst"] = Variable(name="mlotst",\
        preprocess=default,\
        look_for=("mixLyrDpth_mm_uo",)
    )
    variables["siconc"] = Variable(name="siconc",\
        preprocess=tos_siconc,\
        look_for=("iceconc_mm_uo",)
    )
    variables["oceanCurrents"] = Variable(name="oceanCurrents",\
        preprocess=oceanCurrents,\
        look_for=("ucurrTot_ym_dpth","vcurrTot_ym_dpth")
    )    
    variables["height"] = Variable(name="oceanCurrents",\
        preprocess=height,\
        look_for=("ucurrTot_ym_dpth","vcurrTot_ym_dpth")
    )
   
    return variables

if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)