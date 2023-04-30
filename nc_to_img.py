from utils.config import Config
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
import utils.variables.variable_builder as vb
from utils.variables.variable import Variable,retrieve_data
import file_managers.default_manager as default
from file_managers.output_folder import OutputFolder
from utils.logger import Logger,_Logger
import supported_variables.utils.utils as bvu

def load_verticals():
    with open("./vertical-levels.toml",mode="rb") as fp:
        config = tomli.load(fp)
    return config

def load_config(arg_config) -> Config:
    return Config.build(arg_config)

def load_variables(arg_variables,config:Config):
    variables = vb.build(config)
    if arg_variables == "all":
        return variables
    return [variable for variable in variables if variable.name in arg_variables.split(',')]

def save(directory:str):
    def f(inputs:List[Tuple[str,str]]):
        outputs = []
        for input_file,var_name in inputs:
            name = os.path.basename(input_file)
            output = os.path.join(directory,name)
            shutil.copyfile(input_file, output)
            Logger.console().debug(f"\tsave : {output}","SAVE")
            outputs.append((output,var_name))
        return outputs
    return f


def convert_variables(config:Config,variables,ids,files,output,hyper_parameters):
    if files is None:
        files = config.directory
        
    file_manager = default.FileManager.mount(
        input=files,\
        output=output,\
        config=config,\
        variables=variables,\
        ids=ids)
    
    
    for input_files,output_folder,variable,id in file_manager.iter():
        
        logger = Logger.file(output_folder.out(),variable.name)
        output_file = output_folder.out_png_file(f"{id}.{variable.name}")
        hyper_parameters['tmp_directory'] = output_folder.tmp_nc()
        hyper_parameters['logger'] = logger
        for resolution in hyper_parameters['resolutions']:
            hyper_parameters['resolution'] = resolution
            
            nparr_info = retrieve_data(inputs=input_files,\
                variable=variable,\
                hyper_parameters=hyper_parameters,\
                save=save(output_folder.out_nc()))
            res_suffixe = ""
            if resolution < 1:
                res_suffixe = f".r{int(resolution*100)}"
            _output_file = output_file + res_suffixe
            
            png_file = png_converter.convert(input=[data for data,_ in nparr_info],\
                output_filename=_output_file,\
                threshold=hyper_parameters['threshold'],\
                info=nparr_info[0][1],\
                logger=logger)

def main(args):
    
    Logger.blacklist()
    Logger.debug(False)
    Logger.filter("REQUESTS", "CDO INFO","SHAPE","DIMENSION","RESOLUTION")
    Logger.console().info("Starting conversion to png")
    
    config = load_config(args.config)
    variables = load_variables(args.variables,config)
    vertical_levels = load_verticals()
    
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
    
    hyper_parameters = {'resolutions':resolutions,\
        'threshold':threshold,\
        'clean':bool(args.clean),\
        'vertical_levels':vertical_levels}
    
    convert_variables(config=config,\
        variables=variables,\
        ids=args.expids.split(","),\
        files=args.files,\
        output=args.output if args.output is not None else "./",\
        hyper_parameters=hyper_parameters)
    
    Logger.console().info("conversion to png finished ")
    

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--variables',"-v", dest = 'variables', help = 'select variables')
    parser.add_argument('--config',"-c", dest = 'config', help = 'select configurations files')
    parser.add_argument('--experiments',"-e", dest = 'expids', help = 'select experiments')
    parser.add_argument('--files',"-f", dest = 'files', help = 'select file or folder')
    parser.add_argument('--output',"-o", dest = 'output', help = 'select file or folder')
    parser.add_argument('--clean',"-cl",action = 'store_true', help = 'clean the out directory')
    parser.add_argument('--threshold', "-t", dest = "threshold", help = 'specify threshold of maximum and mininum, must be between 0 and 1, default is 0.95')
    parser.add_argument('--resolutions', "-r", dest = "resolutions", help = 'specify resolutions of images must be between 1 and 0, where 1 means 100%% resolutions of netcdf grid input, default is 1')
    
    args = parser.parse_args()
    
    if args.variables is not None and args.config is not None and args.expids is not None:
        main(args)
    else :
        Logger.console().warning(f"Missing arguments \n {parser.format_help()}")
