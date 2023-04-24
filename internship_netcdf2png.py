import utils.png_converter as png_converter

from dataclasses import dataclass
from typing import List,Dict
import os
import shutil
from typing import Tuple
from cdo import Cdo
import tomli
import argparse
from argparse import RawDescriptionHelpFormatter
import variables.variable_builder as vb
from variables.variable import Variable
import file_managers.default_manager as default
from file_managers.output_folder import OutputFolder
import file_managers.bridge.bridge_manager as bridge


def save(input:str,fm:default.FileManager|bridge.BridgeManager):
    def f(files:List[str]):
        output_files = []
        for inputs in files:
            tmp = []
            for path in inputs:
                name = os.path.basename(path)
                output = fm.get_output(input).out_nc_file(name)
                shutil.copyfile(path, output)
                print(f"\tsave : {output}")
                tmp.append(output)
            output_files.append(tmp)
        return output_files
    return f


def convert_file(variable:Variable,threshold:float,input:str,output:OutputFolder,output_file:str,save,inidata=None):
    inputs = variable.open(input,output,save,inidata)
    for input,info in inputs:
        png_converter.convert(input,output_file, threshold,info)
        
def user_convert(file:str, threshold:float, requests:List[dict], clean:bool):
    fm = default.FileManager.mount(file,"./")
    if clean :
        fm.clean()
    
    for input,output in fm.iter():
        for request in requests:   
            print(f"Converting {input} ...")
            output_file = output.out_png_file(os.path.splitext(os.path.basename(input))[0])
            convert_file(variable=request["variable"],\
                threshold=threshold,\
                input=input,\
                output=output,\
                output_file=output_file,\
                save=save(input,fm))

def bridge_convert(file:str,requests:List[dict],filter:List[str],threshold:float,clean:bool):
    fm = bridge.BridgeManager.mount(file,filter = filter)
    if clean :
        fm.clean()
    
    for request in requests:
        for input,output,exp_id in fm.iter(request):  
            suffixe = "".join((f".{name}" for name in os.path.basename(input).split(".")[-2:-1]))
            if suffixe not in (".mm",".sm",".ym"):
                suffixe = ""
            print(f"Converting {exp_id.name} {suffixe.split('.')[-1]} ...")
            output_file = output.out_png_file(f"{exp_id.name}.{request['variable'].name}{suffixe}")
            convert_file(variable=request["variable"],\
                threshold=threshold,\
                input=input,\
                output=output,\
                output_file=output_file,\
                inidata = fm.get_inidata(exp_id),\
                save=save(input,fm))


def load_request():
    with open("./variables.toml",mode="rb") as fp:
        config = tomli.load(fp)
    requests = {}
    clim_variables = vb.builder()
    for variable in config["variables"]:
        if "inidata" in variable:
            requests[variable["output_variable"]] = \
                {
                    "variable":clim_variables[variable["output_variable"]],\
                    "inidata":variable["inidata"],\
                }
        else : 
            requests[variable["output_variable"]] = \
                {
                    "variable":clim_variables[variable["output_variable"]],\
                    "output_stream":variable["output_stream"],\
                    "realm":variable["realm"],\
                }
    return requests

def get_active_requests(args,requests):
    if args.new_variables is not None:
        input_variables = args.new_variables.strip().split(",")
        res = []
        for input in input_variables:
            variable = Variable(name=input,\
                preprocess=vb.default,\
                look_for=(input,)
            )
            res.append({"variable":variable})
        return res
    
    if args.all_bridge_variables:
        raise Exception("NOT IMPLEMENTED : cannot use all variable yet")
        return list(requests.values())
    res = []
    input_variables = args.bridge_variables.strip().split(",")
    for output_variable in input_variables:
        if output_variable in requests:
            res.append(requests[output_variable])
        else :
            raise Exception(f"Wrong variable name : {output_variable}")
            
    return res

def main(args):
    print("Starting conversion to png")
    requests = load_request()
    requests = get_active_requests(args,requests)
    threshold = 0.95 if args.threshold is None else float(args.threshold)

    if args.user is not None:
        user_convert(args.user, threshold, requests, bool(args.clean))
    elif args.bridge is not None and args.new_variables is None:
        if args.expIds is None:
            filter = None
        else :
            filter = args.expIds.strip().split(",")
        bridge_convert(args.bridge,requests,filter, threshold, bool(args.clean))
        
    print("conversion to png finished ")

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--bridge_variables',"-bv", dest = 'bridge_variables', help = 'select brigde variables')
    parser.add_argument('--new_variables',"-nv", dest = 'new_variables', help = 'create new variables with default preprocessing and processing')
    parser.add_argument('--experiences',"-e", dest = 'expIds', help = 'select experince')
    parser.add_argument('--all-bridge-variables',"-av", action = 'store_true', help = 'select all brigde variables')
    parser.add_argument('--user',"-u",dest = "user", help = 'convert the given file or folder')
    parser.add_argument('--bridge',"-b",dest = "bridge", help = 'convert the given file or folder from bridge')
    parser.add_argument('--clean',"-c",action = 'store_true', help = 'clean the out directory')
    parser.add_argument('--threshold', "-t", dest = "threshold", help = 'specify threshold')
 
    args = parser.parse_args()
    if (args.bridge_variables is None and args.new_variables is None) and not args.all_brigde_variables :
        raise Exception(f"Missing arguments \n {parser.format_help()}")
    main(args)