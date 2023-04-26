import utils.png_converter as png_converter

from dataclasses import dataclass
from typing import List,Dict, Union
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
from utils.logger import Logger,_Logger

def save(input:str,fm:Union[default.FileManager,bridge.BridgeManager]):
    def f(files:List[str],resolution):
        output_files = []
        res_suffixe = ".r100"
        if resolution < 1:
            res_suffixe = f".r{int(resolution*100)}"
        for inputs in files:
            tmp = []
            for path in inputs:
                name = os.path.basename(path)
                output = fm.get_output(input).out_nc_file(name) 
                output = output.replace(".nc",f"{res_suffixe}.nc")
                shutil.copyfile(path, output)
                Logger.console().debug(f"\tsave : {output}","SAVE")
                tmp.append(output)
            output_files.append(tmp)
        return output_files
    return f


def convert_file(variable:Variable, hyper_parameters:dict,input:str,output:OutputFolder,output_file:str,save,logger:_Logger,inidata=None):
    try:
        for resolution in hyper_parameters['resolutions']:
            inputs = variable.open(input,output,save,logger,resolution,inidata)
            res_suffixe = ""
            if resolution < 1:
                res_suffixe = f".r{int(resolution*100)}"
            _output_file = output_file + res_suffixe
            for data, metadata in inputs:
                try :
                    metadata.set_resolution(resolution)
                    metadata.set_threshold(hyper_parameters['threshold'])
                    png_converter.convert(data,_output_file, hyper_parameters['threshold'],metadata,logger)
                except Exception as e:
                    trace = Logger.trace()
                    Logger.console().error(trace, "PNG CONVERTER")
                    logger.error(e.__repr__(), "PNG CONVERTER")
    except Exception as e :
        trace = Logger.trace()
        Logger.console().error(trace, "OPEN VARIABLE")
        logger.error(e.__repr__(), "OPEN VARIABLE")


def user_convert(file:str, requests:List[dict], hyper_parameters):
    fm = default.FileManager.mount(file,"./")
    if 'clean' in hyper_parameters and hyper_parameters['clean'] :
        fm.clean()
    
    for input,output in fm.iter():
        for request in requests:  
            Logger.console().info(f"Converting {input} ...")
            logger = Logger.file(fm,input)
            output_file = output.out_png_file(os.path.splitext(os.path.basename(input))[0])
            convert_file(variable=request["variable"],\
                hyper_parameters=hyper_parameters,\
                input=input,\
                output=output,\
                output_file=output_file,\
                logger=logger,\
                save=save(input,fm))

def bridge_convert(file:str,requests:List[dict],hyper_parameters:dict):
    fm = bridge.BridgeManager.mount(file,filter = hyper_parameters['filter'])
    if 'clean' in hyper_parameters and hyper_parameters['clean'] :
        fm.clean()
    for request in requests:
        Logger.console().info(f"\n\trealm : {request['realm']},\n\toutputstream : {request['output_stream']},\n\tvariable : {request['variable'].name}", "REQUEST")
        for input,output,exp_id in fm.iter(request):  
            logger = Logger.file(fm,input)
            suffixe = "".join((f".{name}" for name in os.path.basename(input).split(".")[-3:-2]))
            if suffixe not in (".mm",".sm",".ym"):
                suffixe = ""

            Logger.console().info(f"Converting {exp_id.name} {suffixe.split('.')[-1]} ...")
            output_file = output.out_png_file(f"{exp_id.name}.{request['variable'].name}{suffixe}")
            convert_file(variable=request["variable"],\
                hyper_parameters=hyper_parameters,\
                input=input,\
                output=output,\
                output_file=output_file,\
                inidata = fm.get_inidata(exp_id),\
                logger=logger,\
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
    Logger.blacklist()
    #Logger.debug(False)
    Logger.filter("REQUESTS", "CDO INFO", "SHAPE","DIMENSION","RESOLUTION")
    Logger.console().info("Starting conversion to png")
    requests = load_request()
    requests = get_active_requests(args,requests)

    Logger.console().debug(requests, "REQUESTS")
    if args.threshold is None:
        threshold = 0.95 
    else :
        try:
            threshold = float(args.threshold)
        except :
            threshold = 0.95 
            Logger.console().warning(f"can't convert threshold {args.threshold} to a float, set to default 0.95 instead")
    if args.resolutions is None:
        resolutions = [1] 
    else :
        try:
            resolutions = [float(r) for r in args.resolutions.split(",")]
        except :
            resolutions = [1] 
            Logger.console().warning(f"can't convert resolutions {args.resolutions} to a float, set to default 1 instead")
                
    Logger.console().info(f"threshold : {threshold}")
    Logger.console().info(f"resolutions : {resolutions}")
    
    hyper_parameters = {'resolutions':resolutions,'threshold':threshold,'clean':bool(args.clean)}
    
    if args.user is not None:
        user_convert(args.user, requests, hyper_parameters)
    elif args.bridge is not None and args.new_variables is None:
        if args.expIds is None:
            filter = None
        else :
            filter = args.expIds.strip().split(",")
        hyper_parameters['filter'] = filter
        bridge_convert(args.bridge,requests, hyper_parameters)
        
    Logger.console().info("conversion to png finished ")

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--bridge_variables',"-bv", dest = 'bridge_variables', help = 'select brigde variables')
    parser.add_argument('--new_variables',"-nv", dest = 'new_variables', help = 'create new variables with default preprocessing and processing')
    parser.add_argument('--experiences',"-e", dest = 'expIds', help = 'select experince')
    parser.add_argument('--all-bridge-variables',"-av", action = 'store_true', help = 'select all brigde variables')
    parser.add_argument('--user',"-u",dest = "user", help = 'convert the given file or folder')
    parser.add_argument('--bridge',"-b",dest = "bridge", help = 'convert the given file or folder from bridge')
    parser.add_argument('--clean',"-c",action = 'store_true', help = 'clean the out directory')
    parser.add_argument('--threshold', "-t", dest = "threshold", help = 'specify threshold of maximum and mininum, must be between 0 and 1, default is 0.95')
    parser.add_argument('--resolutions', "-r", dest = "resolutions", help = 'specify resolutions of images must be between 1 and 0, where 1 means 100% resolutions of netcdf grid input, default is 1')
    
    
    args = parser.parse_args()
    
    if (args.bridge_variables is None and args.new_variables is None) and not args.all_bridge_variables :
        raise Exception(f"Missing arguments \n {parser.format_help()}")

    main(args)