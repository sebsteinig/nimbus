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

VERSION = '1.8'


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

def verify_chunks(chunks) :
    try:
        if chunks is not None :
            chunks = float(chunks)
            if chunks > 1 :
                chunks = int(chunks)
            if chunks <0 :
                raise Exception
    except Exception :
        Logger.console().warning(f"the value {chunks} is not valid as a chunks number. Please retry with a positive integer.")
        chunks = None
    return chunks


def convert_variables(config:Config,variables,ids,files,output,hyper_parameters):
    if files is None:
        files = config.hyper_parameters.dir
    
    if os.path.exists(config.hyper_parameters.output_dir) and output == "./":
        output = config.hyper_parameters.output_dir
    
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
            
            id_metadata = {"exp_id":id}
            id_metadata["labels"] = []
            id_metadata["labels"].extend(hyper_parameters["labels"])
            if config.id_metadata is not None:
                parse = config.id_metadata.handle(id)
                id_metadata["metadata"] = parse()
                id_metadata["labels"].extend(config.id_metadata.labels)
            
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
                        
                        chunks_t = hp.chunks_time
                        if hyper_parameters['chunks_t'] is not None:
                            chunks_t = hyper_parameters['chunks_t']
                        
                        chunks_v = hp.chunks_vertical
                        if hyper_parameters['chunks_v'] is not None:
                            chunks_v = hyper_parameters['chunks_v']
                        
                        converters = Converter.build_all(
                            inputs = data,
                            threshold = hp.threshold,
                            metadata = metadata,
                            chunks_t =  chunks_t,
                            chunks_v =  chunks_v,
                            extension = hp.extension,
                            nan_encoding = hp.nan_encoding, 
                            lossless = hp.lossless
                        )
                        list_ts_files = []
                        list_mean_files =[]
                        for converter in converters:
                            ts_files,mean_file = converter.exec()
                            list_ts_files.append(ts_files)
                            list_mean_files.append(mean_file)
                            chunks_t, chunks_v = converter.chunks_t, converter.chunks_v
                            Logger.console().debug(f"Time series : {ts_files}\nMean : {mean_file}","SAVE")
                        
                        logger.info(metadata.log())

                    success += 1
                    archive_db.add(exp_id=id,
                                   variable_name=variable.name,
                                   config_name=config.name,
                                   list_files_ts=list_ts_files,
                                   list_files_mean=list_mean_files,
                                   rx=resolution[0],
                                   ry=resolution[1],
                                   extension=hp.extension.value,
                                   lossless=hp.lossless,
                                   chunks_t= chunks_t, 
                                   chunks_v = chunks_v,
                                   metadata=metadata,
                                   id_metadata=id_metadata
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
        return note,False#archive_db.push()
    else :
        return note,False
    
def main(args):
    start = time.time()
    Logger.blacklist()
    Logger.all(bool(args.debug))
    Logger.filter("REQUESTS", "CDO INFO","SHAPE","DIMENSION","RESOLUTION")
    Logger.console().info("Starting conversion to png")
    
    config = Config.build(args.config)
    variables = load_variables(args.variables,config)

    chunks_t = verify_chunks(args.chunks_t)
    chunks_v = verify_chunks(args.chunks_v)
    
    labels = []
    if args.labels is not None :
        labels.extend(args.labels.split(","))

    hyper_parameters = {'clean':bool(args.clean),
                         'chunks_t':chunks_t, 'chunks_v':chunks_v,"labels":labels}
    
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
    parser.add_argument('--folder',"-f", dest = 'files', help = 'select input folder')
    parser.add_argument('--output',"-o", dest = 'output', help = 'select file or folder')
    parser.add_argument('--clean',"-cl",action = 'store_true', help = 'clean the out directory') 
    parser.add_argument('--debug',"-d", action ='store_true', help = 'add debug information in the log')
    parser.add_argument('--chunkstime',"-ct", dest = 'chunks_t', help = 'specify the number of chunks (in time)') 
    parser.add_argument('--chunksvertical',"-cv", dest = 'chunks_v', help = 'specify the number of chunks (in vertical)') 
    parser.add_argument('--labels',"-l", dest = 'labels', help = 'specify labels') 
    parser.add_argument('--publication',"-p", dest = 'publication', help = 'fill the database with publications information')   
    parser.add_argument('--publicationfolder',"-pf", dest = 'publication_folder', help = 'specify the folder in which to search files')   
    args = parser.parse_args()
    
    if args.publication is not None:
        from api.publication_api import PublicationAPI
        api = PublicationAPI.build(args.publication, args.publication_folder)
        if api is not None :
            api.send()
        
    elif args.variables is not None and args.config is not None and (args.expids is not None or args.files is not None):
        main(args)
    else :
        Logger.console().warning(f"Missing arguments \n {parser.format_help()}")
