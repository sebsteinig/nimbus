import pngConverter
from filenameParser import *
import fileSelector
from dataclasses import dataclass
from typing import List,Dict
import os
import shutil
from typing import Tuple
from cdo import Cdo

@dataclass
class Variable:
    output_variable:pngConverter.OutputVariable
    realm:Realm
    output_stream:OutputStream
    named_input_variable:str

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
        return os.path.join(self.tmp_subfolder(expId.name,"netcdf"),file)
    def path_out_netcdf(self,expId:ExpId,file:str):
        return os.path.join(self.out_subfolder(expId.name,"netcdf"),file)
    def path_out_png(self,expId:ExpId,file:str):
        return os.path.join(self.out_subfolder(expId.name,"png"),file)
    def init(self,expId:ExpId):
        Environment.clean(self.tmp_subfolder(expId.name))
        Environment.clean(self.tmp_subfolder(expId.name,"png"))
        Environment.clean(self.tmp_subfolder(expId.name,"netcdf"))
        Environment.clean(self.out_subfolder(expId.name))
        Environment.clean(self.out_subfolder(expId.name,"png"))
        Environment.clean(self.out_subfolder(expId.name,"netcdf"))
def concatenate(env:Environment):  
    def map(leafs:List[fileSelector.AvgPeriodLeaf]):
        cdo = Cdo()
    
        input_files = []
        for leaf in leafs:
            modelname = leaf.modelname
            netcdf_path = env.path_climate(modelname.expId,modelname.filename)
            tmp_path = env.path_tmp_netcdf(modelname.expId,\
                tmp_file(modelname.expId,\
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
            rename(*model))
        cdo.cat(input = input_files, output = clim_path)
        for tmp_path in input_files:
            os.remove(tmp_path)
        return clim_path,model
    return map
       
def copy_to_tmp(env:Environment,modelnames:List[ModelName]):
    output_files = []
    for modelname in modelnames:
        netcdf_path = env.path_climate(modelname.expId,modelname.filename)
        model = (modelname.expId.name + modelname.realm.value,\
                modelname.output_stream.category + modelname.statistic.value,\
                "clim","ym")
        copy_path = env.path_tmp_netcdf(modelname.expId,\
            rename(*model))
        shutil.copyfile(netcdf_path, copy_path)
        output_files.append((copy_path,model))
    return output_files
        
def inidata_file(expId:ExpId,name:Tuple[str,str]):
    return f"{expId.name}.{name[0]}.{name[1]}.nc"
def tmp_file(expId:ExpId,*extra:str):
    suffixes = "".join([f".{e}" for e in extra])
    return f"{expId.name}{suffixes}.nc"
def rename(*segment:str):
    suffixes = f"{segment[0]}"+ "".join([f".{e}" for e in segment[1:]])
    return f"{suffixes}.nc"

def preprocess_pipeline(variable:Variable):
    match variable.output_variable:
        case pngConverter.OutputVariable.Tos | pngConverter.OutputVariable.Siconc:
            def preprocess(variable:Variable,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                mask_file = env.path_init(expId,inidata_file(expId,("qrparm","omask")))
                lsm_var_file = cdo.selvar("lsm", input = mask_file)
                
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    mapped = cdo.ifnotthen(input=f"{lsm_var_file} {input_path}", options="-r -f nc")
                    
                    shifted_name = rename(*model,"masked","shifted","out")
                    shifted = env.path_tmp_netcdf(expId,shifted_name)
                    #cdo.setmisstonn(input = output1, output = prefix + ".clim.nc", options='-r')
                    cdo.sellonlatbox('-180,180,90,-90',input = mapped, output = shifted)
                    output_files.append(((shifted,shifted_name),))
                
                return output_files
                

        case pngConverter.OutputVariable.OceanCurrents:
            def preprocess(variable:Variable,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    #TODO: check for missing token in the png converter
                    #clean = cdo.setmisstoc(0, input = input_path, options = "-r")

                    int_levels = "10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6"
                    outTmp = cdo.setmisstoc(0, input = f" -intlevel,{int_levels} -selvar,W_ym_dpth {input_path}")
                    
                    remapnn_name = rename(*model,"remapnn","masked","shifted","out")
                    remapnn = env.path_tmp_netcdf(expId,remapnn_name)
                    
                    w_name = rename(*model,"W","masked","shifted","out")
                    wfile = env.path_tmp_netcdf(expId,w_name)
                    
                    cdo.sellonlatbox('-180,180,90,-90',input = input_path, output = remapnn)
                    cdo.sellonlatbox('-180,180,90,-90',input = outTmp, output = wfile)
                    
                    output_files.append(((remapnn,remapnn_name),(wfile,w_name)))
                
                return output_files

        case pngConverter.OutputVariable.Winds:
            def preprocess(variable:Variable,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    name = rename(*model,"shifted","out")
                    out = env.path_tmp_netcdf(expId,name)
                    cdo.sellonlatbox('-180,180,90,-90', input = input_path, output = out)
                    output_files.append(((out,name),))
                return output_files
        case pngConverter.OutputVariable.Liconc:
                def preprocess(variable:Variable,expId:ExpId,env:Environment,files:List[str]):
                    cdo = Cdo()
                    output_files = []
                    for input in files :
                        input_path,model = input
                        #input_path = env.path_tmp_netcdf(expId,input_file)
                        sellevel = cdo.sellevel(9, input = input_path)
                        selvar = cdo.selvar(variable.named_input_variable, input=sellevel)
                        name = rename(*model,"out")
                        out = env.path_tmp_netcdf(expId,name)
                        cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
                        output_files.append(((out,name),))
                    return output_files
        case _:
            def preprocess(variable:Variable,expId:ExpId,env:Environment,files:List[str]):
                cdo = Cdo()
                output_files = []
                for input in files :
                    input_path,model = input
                    #input_path = env.path_tmp_netcdf(expId,input_file)
                    selvar = cdo.selvar(variable.named_input_variable, input=input_path)
                    name = rename(*model,"out")
                    out = env.path_tmp_netcdf(expId,name)
                    cdo.sellonlatbox('-180,180,90,-90', input = selvar, output = out)
                    output_files.append(((out,name),))
                return output_files
    return preprocess

def save(expId:ExpId,env:Environment,files:List[str]):
    output_files = []
    for inputs in files:
        tmp = []
        for input in inputs:
            path,name = input
            output = env.path_out_netcdf(expId,name)
            shutil.copyfile(path, output)
            tmp.append(output)
        output_files.append(tmp)
    return output_files

def convertExpId(env:Environment,expId:ExpId,variable:Variable):
    tree = env.tree.subtree(expIds=[expId],\
        realms=[variable.realm],\
        oss=[variable.output_stream],\
        statistics=[Statistic.TimeMean])
    
    env.init(expId)
    
    #annual_subtree,remaining = tree.split_by(Annual)
    monthly_subtree,_ = tree.split_by(Month)
    monthly_subtree.sort()
    
    preprocess = preprocess_pipeline(variable)
    
    #files = copy_to_tmp(env, annual_subtree.select())
    #files.extend(concatenate(env,monthly_subtree.select()))
    files = [file for file in monthly_subtree.map(fileSelector.StatisticTree,concatenate(env))]
    
    
    preprocessed_files = preprocess(variable,expId,env,files)
    
    nc_files = save(expId,env,preprocessed_files)
    for input_file in nc_files:
        pngConverter.convert_to_png(input_file=input_file[0],\
            expId=expId.name,\
            variable_name=variable.named_input_variable,\
            output_variable=variable.output_variable.value,\
            output_dir=env.path_out_png(expId,""))
    


def main():
    env = Environment.init_environment("./climatearchive_sample_data/data/")
    for expid in env.exps:
        convertExpId(env,expid,Variable(pngConverter.OutputVariable.Clt,Realm.Athmosphere,OutputStream("pd"),"totCloud_mm_ua"))


if __name__ == "__main__" :
    main()