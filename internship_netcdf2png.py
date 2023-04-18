import pngConverter
from filenameParser import *
import fileSelector
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


@dataclass
class Request:
    realm: Realm
    output_stream: OutputStream
    variable: Variable

@dataclass
class Environment:
    tree:fileSelector.ModelTree
    exp_climate_dir:Dict[ExpId,str]
    exp_inidata_dir:Dict[ExpId,str]
    tmp_dir:str
    out_dir:str
    exps:List[ExpId]
    @staticmethod
    def clean(folder:str):
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.mkdir(folder)
    @staticmethod
    def init_filesystem():
        tmp_dir = "./tmp"
        output_dir ="./out"
        Environment.clean(tmp_dir)
        Environment.clean(output_dir)
        return Environment(tree=None,\
            exp_climate_dir=None,\
            exp_inidata_dir=None,\
            tmp_dir=tmp_dir,\
            out_dir=output_dir,\
            exps=None)     
    @staticmethod
    def init_environment(folder:str):
        tree = fileSelector.ModelTree()
        exp_climate_dir = {}
        exp_inidata_dir = {}
        exps = []
        for file in os.listdir(folder):
            d = os.path.join(folder, file)
            if os.path.isdir(d) and ruleExpID(file,0) is not None:
                exp_id = ExpId(file)
                climate_folder = os.path.join(d,"climate")
                inidata_folder = os.path.join(d,"inidata")
                if os.path.isdir(climate_folder) and os.path.isdir(inidata_folder):
                    for filename in fileSelector.load(climate_folder):
                        tree.push(filename)
                    exp_climate_dir[exp_id] = climate_folder
                    #TODO : do the same thing for inidata
                    exp_inidata_dir[exp_id] = inidata_folder
                    exps.append(exp_id)
        tmp_dir = "./tmp"
        output_dir ="./out"
        Environment.clean(tmp_dir)
        Environment.clean(output_dir)
            
        return Environment(tree=tree,\
            exp_climate_dir=exp_climate_dir,\
            exp_inidata_dir=exp_inidata_dir,\
            tmp_dir=tmp_dir,\
            out_dir=output_dir,\
            exps=exps)      
        
    def tmp_subfolder(self,*folder:str):
        return os.path.join(self.tmp_dir,*folder)
    def out_subfolder(self,*folder:str):
        return os.path.join(self.out_dir,*folder)
    
    def path_climate(self,expId:ExpId,file:str):
        return os.path.join(self.exp_climate_dir[expId],file)
    
    def path_init(self,expId:ExpId,file:str):
        return os.path.join(self.exp_inidata_dir[expId],file)
    
    def path_tmp_netcdf(self,expId:ExpId,file:str):
        if expId is None:
            return os.path.join(self.tmp_subfolder("files","netcdf"),file)
        return os.path.join(self.tmp_subfolder(expId.name,"netcdf"),file)
    
    def path_out_netcdf(self,expId:ExpId,file:str):
        if expId is None:
            return os.path.join(self.out_subfolder("files","netcdf"),file)
        return os.path.join(self.out_subfolder(expId.name,"netcdf"),file)
    
    def path_out_png(self,expId:ExpId,file:str):
        if expId is None:
            return os.path.join(self.out_subfolder("files","png"),file)
        return os.path.join(self.out_subfolder(expId.name,"png"),file)
    def path_tmp_png(self,expId:ExpId,file:str):
        if expId is None:
            return os.path.join(self.tmp_subfolder("files","png"),file)
        return os.path.join(self.tmp_subfolder(expId.name,"png"),file)
    def init(self,expId:ExpId):
        if expId is None:
            Environment.clean(self.tmp_subfolder("files"))
            Environment.clean(self.tmp_subfolder("files","png"))
            Environment.clean(self.tmp_subfolder("files","netcdf"))
            Environment.clean(self.out_subfolder("files"))
            Environment.clean(self.out_subfolder("files","png"))
            Environment.clean(self.out_subfolder("files","netcdf"))
            return
        Environment.clean(self.tmp_subfolder(expId.name))
        Environment.clean(self.tmp_subfolder(expId.name,"png"))
        Environment.clean(self.tmp_subfolder(expId.name,"netcdf"))
        Environment.clean(self.out_subfolder(expId.name))
        Environment.clean(self.out_subfolder(expId.name,"png"))
        Environment.clean(self.out_subfolder(expId.name,"netcdf"))
    @staticmethod
    def inidata_file(expId:ExpId,name:Tuple[str,str]):
        return f"{expId.name}.{name[0]}.{name[1]}.nc"
    @staticmethod
    def tmp_file(expId:ExpId,*extra:str):
        suffixes = "".join([f".{e}" for e in extra])
        return f"{expId.name}{suffixes}.nc"
    @staticmethod
    def rename(*segment:str):
        suffixes = f"{segment[0]}"+ "".join([f".{e}" for e in segment[1:]])
        return f"{suffixes}.nc"
    
def concatenate(env:Environment):  
    def map(leafs:List[fileSelector.AvgPeriodLeaf]):
        cdo = Cdo()
    
        input_files = []
        for leaf in leafs:
            modelname = leaf.modelname
            netcdf_path = env.path_climate(modelname.expId,modelname.filename)
            tmp_path = env.path_tmp_netcdf(modelname.expId,\
                Environment.tmp_file(modelname.expId,\
                    modelname.realm.value,\
                    modelname.output_stream.category,\
                    modelname.statistic.value,\
                    modelname.avg_period.mean.value,"tmp"))
            os.system(f"ncatted -a valid_min,,d,, -a valid_max,,d,, {netcdf_path} {tmp_path}")
            input_files.append(tmp_path)
        model = (leafs[0].modelname.expId.name + leafs[0].modelname.realm.value,\
                leafs[0].modelname.output_stream.category + leafs[0].modelname.statistic.value,\
                "clim","mm")
        clim_path = env.path_tmp_netcdf(leafs[0].modelname.expId,\
            Environment.rename(*model))
        cdo.cat(input = input_files, output = clim_path)
        for tmp_path in input_files:
            os.remove(tmp_path)
        return clim_path
    return map
       
def copy_to_tmp(env:Environment,modelnames:List[ModelName]):
    output_files = []
    for modelname in modelnames:
        netcdf_path = env.path_climate(modelname.expId,modelname.filename)
        model = (modelname.expId.name + modelname.realm.value,\
                modelname.output_stream.category + modelname.statistic.value,\
                "clim","ym")
        copy_path = env.path_tmp_netcdf(modelname.expId,\
            Environment.rename(*model))
        shutil.copyfile(netcdf_path, copy_path)
        output_files.append((copy_path,model))
    return output_files

def preprocess_pipeline(variable:Request):
    match variable.output_variable:
        case pngConverter.OutputVariable.Tos | pngConverter.OutputRequest.Siconc:
            def preprocess(variable:Request,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                mask_file = env.path_init(expId,Environment.inidata_file(expId,("qrparm","omask")))
                lsm_var_file = cdo.selvar("lsm", input = mask_file)
                
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input_path}", options="-r -f nc")
                    
                    shifted_name = Environment.rename(*model,"masked","shifted","out")
                    shifted = env.path_tmp_netcdf(expId,shifted_name)
                    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
                    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
                    output_files.append(((shifted,shifted_name),))
                
                return output_files
                

        case pngConverter.OutputVariable.OceanCurrents:
            def preprocess(variable:Request,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    #TODO: check for missing token in the png converter
                    #clean = cdo.setmisstoc(0, input = input_path, options = "-r")

                    int_levels = "10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6"
                    outTmp = cdo.setmisstoc(0, input = f" -intlevel,{int_levels} -selvar,W_ym_dpth {input_path}")
                    
                    remapnn_name = Environment.rename(*model,"remapnn","masked","shifted","out")
                    remapnn = env.path_tmp_netcdf(expId,remapnn_name)
                    
                    w_name = Environment.rename(*model,"W","masked","shifted","out")
                    wfile = env.path_tmp_netcdf(expId,w_name)
                    
                    cdo.sellonlatbox('-180,180,90,-90',input = input_path, output = remapnn)
                    cdo.sellonlatbox('-180,180,90,-90',input = outTmp, output = wfile)
                    
                    output_files.append(((remapnn,remapnn_name),(wfile,w_name)))
                
                return output_files

        case pngConverter.OutputVariable.Winds:
            def preprocess(variable:Request,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    name = Environment.rename(*model,"shifted","out")
                    out = env.path_tmp_netcdf(expId,name)
                    cdo.sellonlatbox('-180,180,90,-90', input = input_path, output = out)
                    output_files.append(((out,name),))
                return output_files
        case pngConverter.OutputVariable.Liconc:
                def preprocess(variable:Request,expId:ExpId,env:Environment,files:List[str]):
                    cdo = Cdo()
                    output_files = []
                    for input in files :
                        input_path,model = input
                        #input_path = env.path_tmp_netcdf(expId,input_file)
                        sellevel = cdo.sellevel(9, input = input_path)
                        selvar = cdo.selvar(variable.named_input_variable, input=sellevel)
                        name = Environment.rename(*model,"out")
                        out = env.path_tmp_netcdf(expId,name)
                        cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
                        output_files.append(((out,name),))
                    return output_files
        case _:
            def preprocess(variable:Request,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    selvar = cdo.selvar(variable.named_input_variable, input=input_path)
                    name = Environment.rename(*model,"out")
                    out = env.path_tmp_netcdf(expId,name)
                    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
                    output_files.append(((out,name),))
                return output_files
    return preprocess

def save(expId:ExpId,env:Environment,files:List[str]):
    output_files = []
    for inputs in files:
        tmp = []
        for path in inputs:
            name = os.path.basename(path)
            output = env.path_out_netcdf(expId,name)
            shutil.copyfile(path, output)
            print(f"\tsave : {output}")
            tmp.append(output)
        output_files.append(tmp)
    return output_files

def convertExpId(env:Environment,expId:ExpId,request:Request):
    print(f"Converting {expId.name} ...")
    tree = env.tree.subtree(expIds=[expId],\
        realms=[request.realm],\
        oss=[request.output_stream],\
        statistics=[Statistic.TimeMean])
    
    monthly_subtree,_ = tree.split_by(Month)
    monthly_subtree.sort()
    files = [file for file in monthly_subtree.map(fileSelector.StatisticTree,concatenate(env))]
    
    
    def _save(files):
        return save(expId,env,files)
    
    def get_inidata_file(*sub_name:str):
        return env.path_init(expId,env.inidata_file(expId,sub_name))
    
    args = {
        "expId":expId,
        "env":env,
        "inidata":get_inidata_file
    }
    inputs = request.variable.open(files,args,_save)
    
    output_dir=env.path_out_png(expId,"")
    output_file=os.path.join(output_dir,f"{expId.name}.{request.variable.name}")
    for input in inputs:
        pngConverter.convert(input,output_file)
    
def convertFile(file:str,request:Request):
    env = Environment.init_filesystem()
    env.init(None)
    filename = os.path.splitext(os.path.basename(file))[0]
    print(f"Converting {filename} ...")
    
    def _save(files):
        return save(None,env,files)
    
    args = {
        "expId":None,
        "env":env
    }
    
    inputs = request.variable.open(file,args,_save)
    
    output_dir=env.path_out_png(None,"")
    output_file=os.path.join(output_dir,f"{filename}")
    for input in inputs:
        pngConverter.convert(input,output_file)
def load_variables():
    with open("./variables.toml",mode="rb") as fp:
        config = tomli.load(fp)
    variables = {}
    clim_variables = vb.builder()
    for variable in config["variables"]:
        variables[variable["output_variable"]] = \
            Request(\
                variable=clim_variables[variable["output_variable"]],\
                output_stream=OutputStream(variable["output_stream"]),\
                realm=Realm(variable["realm"]),\
                )
    return variables

def get_active_variables(args,variables):
    if args.all_variables:
        raise Exception("NOT IMPLEMENTED : cannot use all variable yet")
        return list(variables.values())
    res = []
    input_variables = args.output_variables.strip().split(",")
    for output_variable in input_variables:
        if output_variable in variables:
            res.append(variables[output_variable])
        else :
            raise Exception(f"Wrong variable name : {output_variable}")
            
    return res
def main(args):
    print("Starting conversion to png")
    variables = load_variables()
    variables = get_active_variables(args,variables)
    
    if args.file is not None:
        for variable in variables:
            convertFile(args.file,variable)
    else :
        env = Environment.init_environment("./climatearchive_sample_data/data/")
        for expid in env.exps:
            env.init(expid)
            
        for expid in env.exps:
            for variable in variables:
                convertExpId(env,expid,variable)
    print("conversion to png finished ")

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description = """""", formatter_class = RawDescriptionHelpFormatter)
    parser.add_argument('--output_variables',"-ov", dest = 'output_variables', help = 'select variables')
    parser.add_argument('--all-variables',"-av", action = 'store_true', help = 'takes all variables')
    parser.add_argument('--file',"-f",dest = "file", help = 'convert the given file')
    parser.add_argument('--clean',"-c",action = 'store_true', help = 'clean the out directory')
 
    args = parser.parse_args()
    if args.output_variables is None and not args.all:
        raise Exception(f"Missing arguments \n {parser.format_help()}")
    main(args)