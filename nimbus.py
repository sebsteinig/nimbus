from utils.config import Config
import utils.png_converter as png_converter
from typing import List
import os
import shutil
from typing import Tuple
import argparse
from argparse import RawDescriptionHelpFormatter
import utils.variables.variable_builder as vb
from utils.variables.variable import retrieve_data
import file_managers.default_manager as default
from utils.logger import Logger
import time

VERSION = '1.2'




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
            Logger.console().debug(f"{output}","SAVE")
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

    current_variable = None
    current_id = None
    count_variable = None
    count_id = 0
    
    for input_files,output_folder,variable,id in file_manager.iter():
        if variable != current_variable:
            if count_variable is not None:
                Logger.console().status("conversion of",sep='finished with',variable=current_variable.name,rate=f"{count_id}/{len(ids)}")
            current_variable = variable
            current_id = None
            if count_variable is None:
                count_variable = 0
            if count_id != 0:
                count_variable += 1
            count_id = 0
            Logger.console().status("Starting conversion of", variable=current_variable.name)
        if id != current_id:
            current_id = id
            Logger.console().status("\tStarting conversion of", id=current_id)
        
        logger = Logger.file(output_folder.out_log(),variable.name)
        output_file = output_folder.out_png_file(f"{config.name.lower()}.{id}.{variable.name}")
        hyper_parameters['tmp_directory'] = output_folder.tmp_nc()
        hyper_parameters['logger'] = logger
        error = False
        for resolution in config.get_realm_hp(variable)['resolutions']:
            try : 
                hyper_parameters['resolution'] = resolution
                
                res_suffixe = ""
                if resolution[0] is not None and resolution[1] is not None:
                    res_suffixe = f".rx{resolution[0]}.ry{resolution[1]}"
                _output_file = output_file + res_suffixe
                
                data,metadata = retrieve_data(inputs=input_files,\
                    variable=variable,\
                    hyper_parameters=hyper_parameters,\
                    config=config,\
                    output_file = _output_file,\
                    save=save(output_folder.out_nc()))
                
                
                metadata.extends(version = VERSION)
                
                png_file = png_converter.convert(inputs=data,\
                    threshold=config.get_hp(variable.name).threshold,\
                    metadata=metadata,\
                    logger=logger)
                Logger.console().debug(f"{png_file}","SAVE")
                logger.info(metadata.log(),"METADATA")
            except Exception as e:
                error = True
                trace = Logger.trace() 
                Logger.console().error(trace, "PNG CONVERTER")
                logger.error(e.__repr__(), "PNG CONVERTER")
        if not error :
            count_id += 1 
    if count_variable is not None:
        Logger.console().status("conversion of",sep=' finished with ',variable=current_variable.name,rate=f"{count_id}/{len(ids)}")
    if count_id != 0:
        count_variable += 1
    return count_variable,len(variables)



def main(args):
    start = time.time()
    Logger.blacklist()
    Logger.debug(bool(args.debug))
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
    
    
    end = time.time()
    if success == total:
        Logger.console().success(success,total,end-start)
    else :
        Logger.console().failure(success,total,end-start)
        
 

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--variables',"-v", dest = 'variables', help = 'select variables')
    parser.add_argument('--config',"-c", dest = 'config', help = 'select configurations files')
    parser.add_argument('--experiments',"-e", dest = 'expids', help = 'select experiments')
    parser.add_argument('--files',"-f", dest = 'files', help = 'select file or folder')
    parser.add_argument('--output',"-o", dest = 'output', help = 'select file or folder')
    parser.add_argument('--clean',"-cl",action = 'store_true', help = 'clean the out directory') 
    parser.add_argument('--debug',"-d", action ='store_true', help = 'add debug information in the log')    
    args = parser.parse_args()
    
    if args.variables is not None and args.config is not None and (args.expids is not None or args.files is not None):
        main(args)
    else :
        Logger.console().warning(f"Missing arguments \n {parser.format_help()}")
