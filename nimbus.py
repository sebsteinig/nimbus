from api.archive_db import ArchiveDB
from utils.config import Config
from utils.converters.converter import Converter
from typing import List
import os
import shutil
from typing import Tuple
import argparse
from argparse import RawDescriptionHelpFormatter
import utils.variables.variable_builder as vb
from utils.variables.variable import VariableNotFoundError, retrieve_data,preprocess
import file_managers.default_manager as default
from utils.logger import Logger
import time

VERSION = '1.3'



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
        files = config.hyper_parameters.dir
        
    if hyper_parameters['clean']:
        default.FileManager.clean(ids, output)

    archive_db = ArchiveDB.build()

    with default.FileManager.mount(
        input=files,\
        output=output,\
        config=config,\
        variables=variables,\
        ids=ids) as file_manager:

        file_manager.clusterize()

        note = {}
            
        for id in file_manager.iter_id():
            Logger.console().status("Starting conversion of", id=id)
            success = 0
            total = 0
            status = 0
            
            var_note = {}
            for variable,output_folder,bind in file_manager.iter_variables_from(id):
                hp = config.get_hp(variable.name)
                Logger.console().progress_bar(var_name=variable.name,id = id)  
                total += 1
                Logger.console().status("\tStarting conversion of", id=id)
                logger = Logger.file(output_folder.out_log(),variable.name)
                output_file = output_folder.out_img_file(f"{config.name.lower()}.{id}.{variable.name}")
                hyper_parameters['tmp_directory'] = output_folder.tmp_nc()
                hyper_parameters['logger'] = logger
                
                try:
                    files_var_binder = list(bind(id))
                    files_var_binder = preprocess(files_var_binder,variable,output_folder.tmp_nc(),file_manager.file_cluster_binder[id])
                
                    
                    for resolution in config.get_realm_hp(variable)['resolutions']:
                        hyper_parameters['resolution'] = resolution
                            
                        res_suffixe = ""
                        if resolution[0] is not None and resolution[1] is not None:
                            res_suffixe = f".rx{resolution[0]}.ry{resolution[1]}"
                        _output_file = output_file + res_suffixe
                        
                        data,metadata = retrieve_data(inputs=files_var_binder,\
                            variable=variable,\
                            hyper_parameters=hyper_parameters,\
                            config=config,\
                            output_file = _output_file,\
                            save=save(output_folder.out_nc()))
                        
                        
                        metadata.extends(version = VERSION)
                        
                        chunks = hp.chunks
                        if hyper_parameters['chunks'] is not None:
                            chunks = hyper_parameters['chunks']
                        
                        converters = Converter.build_all(
                            inputs = data,
                            threshold = hp.threshold,
                            metadata = metadata,
                            chunks =  chunks,
                            extension = hp.extension,
                            nan_encoding = hp.nan_encoding, 
                            lossless = hp.lossless
                        )
                        list_ts_files = []
                        list_mean_files =[]
                        for converter in converters:
                            ts_files,mean_file = converter.exec()
                            list_ts_files.extend(ts_files)
                            list_mean_files.append(mean_file)
                            Logger.console().debug(f"Time series : {ts_files}\nMean : {mean_file}","SAVE")
                        
                        logger.info(metadata.log(),"METADATA")

                    success += 1
                    archive_db.add(exp_id=id,
                                   variable_name=variable.name,
                                   config_name=config.name,
                                   files_ts=list_ts_files,
                                   files_mean=list_mean_files,
                                   rx=resolution[0],
                                   ry=resolution[1],
                                   extension=hp.extension.value,
                                   lossless=hp.lossless,
                                   chunks=chunks,
                                   metadata=metadata
                                   )
                except VariableNotFoundError as e :
                    Logger.console().warning(f"Variable {e.args[0]} not found for {id} in {variable.name}")
                    status = 1
                except Exception as e:
                    status = -1
                    trace = Logger.trace() 
                    Logger.console().error(trace, "PNG CONVERTER")
                    logger.error(e.__repr__(), "PNG CONVERTER")   
                Logger.console().status("conversion finished for",id=id)
                var_note[variable.name] = status

            note[id] = ((success,total),var_note)
            Logger.console().status("conversion finished for",variable=variable.name)

    if all( all(status != -1 for status in var_note.values()) for (_,_),var_note in note.values()):
        archive_db.commit()
        return note,archive_db.push()
    else :
        return note,False
def main(args):
    start = time.time()
    Logger.blacklist()
    Logger.all(bool(args.debug))
    Logger.filter("REQUESTS", "CDO INFO","SHAPE","DIMENSION","RESOLUTION")
    Logger.console().info("Starting conversion to png")
    
    config = load_config(args.config)
    variables = load_variables(args.variables,config)
    try:
        chunks = args.chunks
        if chunks is not None :
            chunks = float(chunks)
            if chunks > 1 :
                chunks = int(chunks)
            if chunks <0 :
                raise Exception
    except Exception :
        Logger.console().warning(f"the value {args.chunks} is not valid as a chunks number. Please retry with a positive integer.")
        chunks = None
    hyper_parameters = {'clean':bool(args.clean),
                        'chunks':chunks}
    
    note,push_success = convert_variables(config=config,\
        variables=variables,\
        ids= None if args.expids is None else args.expids.split(","),\
        files=args.files,\
        output=args.output if args.output is not None else "./",\
        hyper_parameters=hyper_parameters)
    
    
    end = time.time()    
    if all( all(status != -1 for status in var_note.values()) for (_,_),var_note in note.values()):
        Logger.console().success(note,end-start,push_success)
    else :
        Logger.console().failure(note,end-start,push_success)
    
        
 

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--variables',"-v", dest = 'variables', help = 'select variables')
    parser.add_argument('--config',"-c", dest = 'config', help = 'select configurations files')
    parser.add_argument('--experiments',"-e", dest = 'expids', help = 'select experiments')
    parser.add_argument('--files',"-f", dest = 'files', help = 'select file or folder')
    parser.add_argument('--output',"-o", dest = 'output', help = 'select file or folder')
    parser.add_argument('--clean',"-cl",action = 'store_true', help = 'clean the out directory') 
    parser.add_argument('--debug',"-d", action ='store_true', help = 'add debug information in the log')
    parser.add_argument('--chunks',"-ch", dest = 'chunks', help = 'specify the number of output images')    
    args = parser.parse_args()
    
    if args.variables is not None and args.config is not None and (args.expids is not None or args.files is not None):
        main(args)
    else :
        Logger.console().warning(f"Missing arguments \n {parser.format_help()}")
