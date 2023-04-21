if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)

from file_managers.default_manager import FileManager,assert_nc_extension,file_name
from file_managers.output_folder import OutputFolder
import os.path as path
from os import mkdir,listdir,system,remove
import shutil
from typing import List,Dict
if __name__ == "__main__":
    import bridge.bridge_filename_parser as parser
    import bridge.bridge_file_selector as selector
else :
    import file_managers.bridge.bridge_filename_parser as parser
    import file_managers.bridge.bridge_file_selector as selector
    
from cdo import Cdo

class BridgeManager:
    def __init__(self,output:Dict[parser.ExpId,OutputFolder],tree:selector.BridgeTree,selected_expid:List[parser.ExpId]):
        self.input = {}
        self.output = output
        self.tree = tree
        self.selected_expid = selected_expid
    
    def get_output(self,input) -> OutputFolder:
        return self.output[self.input[input]]
    
    
    def clean(self):
        for folder in self.output.values():
            if path.exists(folder.out_nc()):
                shutil.rmtree(folder.out_nc())
            mkdir(folder.out_nc())
            if path.exists(folder.out_png()):
                shutil.rmtree(folder.out_png())
            mkdir(folder.out_png())
    
    def iter(self,request):
        tree = self.tree.subtree(expIds=self.selected_expid,\
            realms=[parser.Realm(request["realm"])],\
            oss=[parser.OutputStream(request["output_stream"])],\
            statistics=[parser.Statistic.TimeMean]
            )
        tree.sort()
        for input_files,exp_id in tree.map(selector.StatisticTree,self.concatenate()):
            for input_file in input_files:
                self.input[input_file] = exp_id
                yield input_file,self.output[exp_id],exp_id
                
    def concatenate(self):
        def map(leafs:List[selector.AvgPeriodLeaf]):
            cdo = Cdo()
            
            monthly_leaf = [leaf for leaf in leafs if type(leaf.bridge_name.avg_period.mean) is parser.Month]
            annual_leaf = [leaf for leaf in leafs if type(leaf.bridge_name.avg_period.mean) is parser.Annual]
            seasonal_leaf = [leaf for leaf in leafs if type(leaf.bridge_name.avg_period.mean) is parser.Season]
            
            output_paths = []
            
            if len(monthly_leaf) > 0:
                output_paths.append(BridgeManager.__concatenate(monthly_leaf,self.output,cdo,"mm"))
             
            if len(annual_leaf) == 1:
                annual_leaf = annual_leaf[0]
                bridge_name:parser.BridgeName = annual_leaf.bridge_name
                output_path = bridge_name.filepath.replace("ann.nc", ".clim.ym.nc") 
                output_path = self.output[bridge_name.expId].tmp_nc_file(file_name(output_path))
                shutil.copyfile(bridge_name.filepath, output_path)
                output_paths.append(output_path)
                
            if len(seasonal_leaf) > 0:
                output_paths.append(BridgeManager.__concatenate(seasonal_leaf,self.output,cdo,"sm"))
 
            return output_paths,leafs[0].bridge_name.expId
        return map

    @staticmethod
    def __concatenate(leafs:List[selector.AvgPeriodLeaf],output,cdo,suffixe):
        leaf_tmp_file = []
        for leaf in leafs:
            bridge_name:parser.BridgeName = leaf.bridge_name
            netcdf_path = bridge_name.filepath
            tmp_path = output[bridge_name.expId].tmp_nc_file(file_name(netcdf_path).replace(".nc",".tmp.nc"))
            system(f"ncatted -a valid_min,,d,, -a valid_max,,d,, {netcdf_path} {tmp_path}")
            leaf_tmp_file.append(tmp_path)
            
        bridge_name:parser.BridgeName = leafs[0].bridge_name
        
        output_path = "".join((f"{bridge_name.expId.name}",\
            f"{bridge_name.realm.value}",\
            f".{bridge_name.output_stream.category}",\
            f"{bridge_name.statistic.value}",\
            f".clim.{suffixe}.nc"
            ))
        output_path = output[leafs[0].bridge_name.expId].tmp_nc_file(output_path)
        cdo.cat(input = leaf_tmp_file, output = output_path)
        for tmp_path in leaf_tmp_file:
            remove(tmp_path)
        return output_path

    @staticmethod
    def __mount_output(output:str):
        main = path.join(output,"nc_to_png_outputs")
        if not path.isdir(main):
            mkdir(main)
        out = path.join(main,"output")
        if not path.isdir(out):
            mkdir(out)
        tmp = path.join(main,"tmp")
        if not path.isdir(tmp):
            mkdir(tmp)
        return OutputFolder(main_dir=main,out_dir=out,tmp_dir=tmp)

    @staticmethod
    def __mount_expid(expid:parser.ExpId,folder:OutputFolder) -> OutputFolder:
        out = folder.append(expid.name)
        out.mount()
        return out


    @staticmethod
    def __mount_file(input:str,output:str,filter:list):
        if not assert_nc_extension(input):
            raise Exception(f"{input} is not a netCDF file")
        
        out_folder = BridgeManager.__mount_output(output)
        input_bridge = parser.parse(input)
        
        if filter is not None and input_bridge.expId not in filter:
            raise Exception(f"The provided file {input} does not math any of the experience id in {filter}")
        
        out_folder = BridgeManager.__mount_expid(expid=input_bridge.expId,folder= out_folder)
        
        tree = selector.BridgeTree()
        tree.push(input_bridge)
        #shutil.copyfile(input, out_folder.tmp_nc_file(file_name(input)))
        
        return BridgeManager(\
            output = {input_bridge.expId:out_folder},\
            tree = tree,\
            selected_expid = [input_bridge.expId])
        
    
    @staticmethod
    def __mount_folder(input:str,output:str,filter:list):
        out_folder = BridgeManager.__mount_output(output)
        
        tree = selector.BridgeTree()
        output:dict = {}
        
        selected_expid = []
        
        for file in listdir(input):
            d = path.join(input, file)
            if path.isdir(d) and parser.ruleExpID(file,0) is not None and ((filter is not None and file in filter) or (filter is None)):
                exp_id = parser.ExpId(file)
                selected_expid.append(exp_id)
                climate_folder = path.join(d,"climate")
                inidata_folder = path.join(d,"inidata")
                if path.isdir(climate_folder) and path.isdir(inidata_folder):
                    folder:OutputFolder =  BridgeManager.__mount_expid(expid=exp_id,folder= out_folder)
                    output[exp_id] = folder
                    for filename in selector.load(climate_folder):
                        tree.push(filename)
        return  BridgeManager(\
            output = output,\
            tree = tree,\
            selected_expid = selected_expid)
    
    @staticmethod
    def mount(input:str,filter:list=None,output:str="./"):
        if not path.isdir(output):
            raise Exception(f"{output} is not a folder")
        if not path.exists(input):
            raise Exception(f"{input} does not exist")
        
        match input:
            case file if path.isfile(input):
                return BridgeManager.__mount_file(input,output,filter)
            case folder if path.isdir(input):
                return BridgeManager.__mount_folder(input,output,filter)    