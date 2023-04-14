from os import walk
import filenameParser
from dataclasses import dataclass, field
from typing import List
from filenameParser import *
from typing import Type,Union,Callable,Any
@dataclass
class AvgPeriodLeaf:
    node:AvgPeriod
    modelname:ModelName
    def select(self)->ModelName:
        #return self.filename
        yield self.modelname
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is AvgPeriodLeaf :
            yield function([self.modelname])
        else :
            return None 
@dataclass
class StatisticTree:
    node:Statistic
    branches:List[AvgPeriodLeaf] = field(default_factory=list)
    def push(self,filename:ModelName):
        branch = AvgPeriodLeaf(filename.avg_period,filename)
        self.branches.append(branch)
    def subtree(self,avgperiods:List[AvgPeriod]=[]):
        if avgperiods is None or len(avgperiods)==0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in avgperiods:
                 sub_branches.append(branch)
        return StatisticTree(node=self.node,branches=sub_branches)
    def select(self)->ModelName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[Annual],Type[Month],Type[Season]]):
        period_type = None
        match period:
            case _ if period is Annual:
                period_type = Annual
            case _ if period is Month:
                period_type = Month
            case _ if period is Season:
                period_type = Season
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
    node:OutputStream
    branches:List[StatisticTree] = field(default_factory=list)
    def push(self,filename:ModelName):
        for branch in self.branches:
            if filename.statistic == branch.node:
                branch.push(filename)
                return
        branch = StatisticTree(filename.statistic)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            statistics:List[Statistic]=[],\
            avgperiods:List[AvgPeriod]=[]):
        if statistics is None or len(statistics) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in statistics:
                 sub_branches.append(branch.subtree(avgperiods))
        return OutputStreamTree(node=self.node,branches=sub_branches)
    def select(self)->ModelName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[Annual],Type[Month],Type[Season]]):
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
    node:Realm
    branches:List[OutputStreamTree] = field(default_factory=list)
    def push(self,filename:ModelName):
        for branch in self.branches:
            if filename.output_stream == branch.node:
                branch.push(filename)
                return
        branch = OutputStreamTree(filename.output_stream)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            oss:List[OutputStream]=[],\
            statistics:List[Statistic]=[],\
            avgperiods:List[AvgPeriod]=[]):
        if oss is None or len(oss) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in oss:
                 sub_branches.append(branch.subtree(statistics,avgperiods))
        return RealmTree(node=self.node,branches=sub_branches)
    def select(self)->ModelName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[Annual],Type[Month],Type[Season]]):
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
    node:ExpId
    branches:List[RealmTree] = field(default_factory=list)
    def push(self,filename:ModelName):
        for branch in self.branches:
            if filename.realm == branch.node:
                branch.push(filename)
                return
        branch = RealmTree(filename.realm)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            realms:List[Realm]=[],\
            oss:List[OutputStream]=[],\
            statistics:List[Statistic]=[],\
            avgperiods:List[AvgPeriod]=[]):
        if realms is None or len(realms) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in realms:
                 sub_branches.append(branch.subtree(oss,statistics,avgperiods))
        return ExpTree(node=self.node,branches=sub_branches)
    def select(self)->ModelName:
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[Annual],Type[Month],Type[Season]]):
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
class ModelTree:
    branches:List[ExpTree] = field(default_factory=list)
    def push(self,filename:ModelName):
        for branch in self.branches:
            if filename.expId == branch.node:
                branch.push(filename)
                return
        branch = ExpTree(filename.expId)
        branch.push(filename)
        self.branches.append(branch)
    def subtree(self,\
            expIds:List[ExpId]=[],\
            realms:List[Realm]=[],\
            oss:List[OutputStream]=[],\
            statistics:List[Statistic]=[],\
            avgperiods:List[AvgPeriod]=[]):
        if expIds is None or len(expIds) == 0: return self
        sub_branches = []
        for branch in self.branches:
            if branch.node in expIds:
                 sub_branches.append(branch.subtree(realms,oss,statistics,avgperiods))
        return ModelTree(sub_branches)
    def select(self):
        #res = []
        for branch in self.branches:
            #res.extend(branch.select())
            yield from branch.select()
        #return res
    def split_by(self,period:Union[Type[Annual],Type[Month],Type[Season]]):
        sub_1 = []
        sub_2 = []
        for branch in self.branches:
            _1,_2 = branch.split_by(period)
            sub_1.append(_1)
            sub_2.append(_2)
        return ModelTree(branches=sub_1),ModelTree(branches=sub_2)
    def sort(self):
        for branch in self.branches:
            branch.sort()
            
    def map(self,level:Type,function:Callable[[List],Any]):
        if level is ModelTree :
            yield function(self.branches)
        else :
            for branch in self.branches:
                yield from branch.map(level,function)
def load(folder:str):
    for filename in next(walk(folder))[2]:
        yield parse(filename)

def push(filename:ModelName,tree:ModelTree)->ModelTree:
    tree.push(filename)


def testMap(hyper):
    def f(arr):
        print(f"f on {len(arr)} with {hyper}")
        return 1
    return f

def test():
    tree = ModelTree()
    for filename in load("./climatearchive_sample_data/data/texpa1/climate"):
        tree.push(filename)
    print([f.filename for f in tree.subtree(expIds=[ExpId("texpa1")],\
        realms=[Realm.Athmosphere],\
        oss=[OutputStream("rd"),OutputStream("pt")],\
        statistics=[Statistic.TimeMean],\
        avgperiods=[AvgPeriod(Month.Jan)]).select()])
    
    print([file for file in tree.map(StatisticTree,testMap("env"))])

if __name__ == "__main__":
    test()