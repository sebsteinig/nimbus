from dataclasses import dataclass, field
from typing import List
import os.path as path
from os import listdir
if __name__ == "__main__":
    import bridge_filename_parser as parser
else :
    import file_managers.bridge.bridge_filename_parser as parser
    
from typing import Type,Union,Callable,Any

@dataclass
class AvgPeriodLeaf:
    node:parser.AvgPeriod
    bridge_name:parser.BridgeName
    def select(self)->parser.BridgeName:
        #return self.filename
        yield self.bridge_name
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is AvgPeriodLeaf :
            yield function([self.bridge_name])
        else :
            return None 
@dataclass
class StatisticTree:
    node:parser.Statistic
    branches:List[AvgPeriodLeaf] = field(default_factory=list)
    def push(self,filename:parser.BridgeName):
        branch = AvgPeriodLeaf(filename.avg_period,filename)
        self.branches.append(branch)
    def subtree(self,avgperiods:List[parser.AvgPeriod]=[]):
        if avgperiods is None or len(avgperiods)==0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in avgperiods:
                 sub_branches.append(branch)
        return StatisticTree(node=self.node,branches=sub_branches)
    def select(self)->parser.BridgeName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[parser.Annual],Type[parser.Month],Type[parser.Season]]):
        period_type = None
        match period:
            case _ if period is parser.Annual:
                period_type = parser.Annual
            case _ if period is parser.Month:
                period_type = parser.Month
            case _ if period is parser.Season:
                period_type = parser.Season
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            if type(branch.node.mean) is period_type:
                sub_1.append(branch)
            else :
                sub_2.append(branch)
        return StatisticTree(node=self.node,branches=sub_1),StatisticTree(node=self.node,branches=sub_2)
    def sort(self):
        self.branches.sort(key=lambda v:v.node.mean.key())
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is StatisticTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function) 
@dataclass
class OutputStreamTree:
    node:parser.OutputStream
    branches:List[StatisticTree] = field(default_factory=list)
    def push(self,filename:parser.BridgeName):
        for branch in self.branches:
            if filename.statistic == branch.node:
                branch.push(filename)
                return
        branch = StatisticTree(filename.statistic)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            statistics:List[parser.Statistic]=[],\
            avgperiods:List[parser.AvgPeriod]=[]):
        if statistics is None or len(statistics) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in statistics:
                 sub_branches.append(branch.subtree(avgperiods))
        return OutputStreamTree(node=self.node,branches=sub_branches)
    def select(self)->parser.BridgeName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[parser.Annual],Type[parser.Month],Type[parser.Season]]):
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            _1,_2 = branch.split_by(period)
            sub_1.append(_1)
            sub_2.append(_2)
        return OutputStreamTree(node=self.node,branches=sub_1),OutputStreamTree(node=self.node,branches=sub_2)
    def sort(self):
        for branch in self.branches:
            branch.sort()
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is OutputStreamTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function)        
@dataclass
class RealmTree:
    node:parser.Realm
    branches:List[OutputStreamTree] = field(default_factory=list)
    def push(self,filename:parser.BridgeName):
        for branch in self.branches:
            if filename.output_stream == branch.node:
                branch.push(filename)
                return
        branch = OutputStreamTree(filename.output_stream)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            oss:List[parser.OutputStream]=[],\
            statistics:List[parser.Statistic]=[],\
            avgperiods:List[parser.AvgPeriod]=[]):
        if oss is None or len(oss) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in oss:
                 sub_branches.append(branch.subtree(statistics,avgperiods))
        return RealmTree(node=self.node,branches=sub_branches)
    def select(self)->parser.BridgeName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[parser.Annual],Type[parser.Month],Type[parser.Season]]):
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            _1,_2 = branch.split_by(period)
            sub_1.append(_1)
            sub_2.append(_2)
        return RealmTree(node=self.node,branches=sub_1),RealmTree(node=self.node,branches=sub_2)
    def sort(self):
        for branch in self.branches:
            branch.sort()
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is RealmTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function)
@dataclass
class ExpTree:
    node:parser.ExpId
    branches:List[RealmTree] = field(default_factory=list)
    def push(self,filename:parser.BridgeName):
        for branch in self.branches:
            if filename.realm == branch.node:
                branch.push(filename)
                return
        branch = RealmTree(filename.realm)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            realms:List[parser.Realm]=[],\
            oss:List[parser.OutputStream]=[],\
            statistics:List[parser.Statistic]=[],\
            avgperiods:List[parser.AvgPeriod]=[]):
        if realms is None or len(realms) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in realms:
                 sub_branches.append(branch.subtree(oss,statistics,avgperiods))
        return ExpTree(node=self.node,branches=sub_branches)
    def select(self)->parser.BridgeName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[parser.Annual],Type[parser.Month],Type[parser.Season]]):
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            _1,_2 = branch.split_by(period)
            sub_1.append(_1)
            sub_2.append(_2)
        return ExpTree(node=self.node,branches=sub_1),ExpTree(node=self.node,branches=sub_2)
    def sort(self):
        for branch in self.branches:
            branch.sort()
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is ExpTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function)
@dataclass
class BridgeTree:
    branches:List[ExpTree] = field(default_factory=list)
    def push(self,filename:parser.BridgeName):
        for branch in self.branches:
            if filename.expId == branch.node:
                branch.push(filename)
                return
        branch = ExpTree(filename.expId)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            expIds:List[parser.ExpId]=[],\
            realms:List[parser.Realm]=[],\
            oss:List[parser.OutputStream]=[],\
            statistics:List[parser.Statistic]=[],\
            avgperiods:List[parser.AvgPeriod]=[]):
        if expIds is None or len(expIds) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in expIds:
                 sub_branches.append(branch.subtree(realms,oss,statistics,avgperiods))
        return BridgeTree(sub_branches)
    def select(self):
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[parser.Annual],Type[parser.Month],Type[parser.Season]]):
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            _1,_2 = branch.split_by(period)
            sub_1.append(_1)
            sub_2.append(_2)
        return BridgeTree(branches=sub_1),BridgeTree(branches=sub_2)
    def sort(self):
        for branch in self.branches:
            branch.sort()
            
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is BridgeTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function)
                
def assert_nc_extension(file:str):
    return path.basename(file).split(".")[-1] == "nc"

def load(folder:str):
    for name in listdir(folder):
        file = path.join(folder,name)
        if path.isfile(file) and assert_nc_extension(file):
            yield parser.parse(file)

def push(filename:parser.BridgeName,tree:BridgeTree)->BridgeTree:
    tree.push(filename)


def testMap(hyper):
    def f(arr):
        print(f"f on {len(arr)} with {hyper}")
        return 1
    return f

def test():
    tree = BridgeTree()
    for filename in load("./climatearchive_sample_data/data/texpa1/climate"):
        tree.push(filename)
    print([f.filepath for f in tree.subtree(expIds=[parser.ExpId("texpa1")],\
        realms=[parser.Realm.Athmosphere],\
        oss=[parser.OutputStream("rd"),parser.OutputStream("pt")],\
        statistics=[parser.Statistic.TimeMean],\
        avgperiods=[parser.AvgPeriod(parser.Month.Jan)]).select()])
    
    print([file for file in tree.map(StatisticTree,testMap("env"))])

if __name__ == "__main__":
    test()