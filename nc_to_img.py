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


VERSION = '1.0'


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
        
    if hyper_parameters['clean']:
        default.FileManager.clean(ids, output)

    file_manager = default.FileManager.mount(
        input=files,\
        output=output,\
        config=config,\
        variables=variables,\
        ids=ids)

    nb_success_png_count = 0
    nb_png_total = 0
    for input_files,output_folder,variable,id in file_manager.iter():
        logger = Logger.file(output_folder.out(),variable.name)
        output_file = output_folder.out_png_file(f"{id}.{variable.name}")
        hyper_parameters['tmp_directory'] = output_folder.tmp_nc()
        hyper_parameters['logger'] = logger
        for resolution in config.get_hp(variable.name).resolutions:
            nb_png_total += 1
            try : 
                hyper_parameters['resolution'] = resolution
                
                data,metadata = retrieve_data(inputs=input_files,\
                    variable=variable,\
                    hyper_parameters=hyper_parameters,\
                    config=config,\
                    save=save(output_folder.out_nc()))
                
                res_suffixe = ""
                if resolution[0] is not None and resolution[1] is not None:
                    res_suffixe = f".rx{resolution[0]}.ry{resolution[1]}"
                _output_file = output_file + res_suffixe
                
                metadata.extends(version = VERSION)
                png_file = png_converter.convert(input=data,\
                    output_filename=_output_file,\
                    threshold=config.get_hp(variable.name).threshold,\
                    metadata=metadata,\
                    logger=logger)
                Logger.console().debug(f"\tsave : {png_file}","SAVE")
                logger.info(metadata.log(),"METADATA")
                nb_success_png_count += 1
            except Exception as e:
                trace = Logger.trace() 
                Logger.console().error(trace, "PNG CONVERTER")
                logger.error(e.__repr__(), "PNG CONVERTER")
    return nb_success_png_count,nb_png_total



def main(args):
    
    Logger.blacklist()
    Logger.debug(True)
    Logger.filter("REQUESTS", "CDO INFO","SHAPE","DIMENSION","RESOLUTION")
    Logger.console().info("Starting conversion to png")
    
    config = load_config(args.config)
    variables = load_variables(args.variables,config)
    

    hyper_parameters = {'clean':bool(args.clean),}
    
    success,total = convert_variables(config=config,\
        variables=variables,\
        ids= None if args.expids is None else args.expids.split(","),\
        files=args.files,\
        output=args.output if args.output is not None else "./",\
        hyper_parameters=hyper_parameters)
    
    Logger.console().info(f"conversion to png finished with {success}/{total} successes")
    

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--variables',"-v", dest = 'variables', help = 'select variables')
    parser.add_argument('--config',"-c", dest = 'config', help = 'select configurations files')
    parser.add_argument('--experiments',"-e", dest = 'expids', help = 'select experiments')
    parser.add_argument('--files',"-f", dest = 'files', help = 'select file or folder')
    parser.add_argument('--output',"-o", dest = 'output', help = 'select file or folder')
    parser.add_argument('--clean',"-cl",action = 'store_true', help = 'clean the out directory')    
    args = parser.parse_args()
    
    if args.variables is not None and args.config is not None and (args.expids is not None or args.files is not None):
        main(args)
    else :
        Logger.console().warning(f"Missing arguments \n {parser.format_help()}")
