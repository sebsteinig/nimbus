from dataclasses import dataclass
import traceback
from datetime import datetime
import os

@dataclass
class _Logger:
    std_output: str | None
    def debug(self):
        pass
    
    def warning(self):
        pass
    
    def info(self):
        pass
    
    def error(self):
        pass
    
class Logger:
    @staticmethod
    def console() -> _Logger:
        pass
    
    @staticmethod
    def file() -> _Logger:
        pass


def logErrorForAll(err):
    logFile = open(datetime.now().strftime("%d%m%Y_%H:%M:%S") + ".log", "a")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n\n\n\n{err.args[0]}")
    logFile.close()

def logErrorForVarAndExpid(outputFolder, variable, expid, err):
    logFile = open(os.path.join(outputFolder,f"{expid}{variable}{datetime.now().strftime('%d%m%Y_%H:%M:%S')}.log"), "a")
    logFile.write(f"-------------error when converting experience : {expid} with variable : {variable}---------------\n")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n : {err.args[0]}")
    logFile.close()

def logErrorForVar(outputFolder, variable, err):
    logFile = open(os.path.join(outputFolder, f"{variable}{datetime.now().strftime('%d%m%Y_%H:%M:%S')}.log"), "a")
    logFile.write(f"-------------error when converting with variable : {variable}---------------\n")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n : {err.args[0]}")
    logFile.close()

    
def test():
    Logger.console().debug()

if __name__ == "__main__":
    #print("Cannot execute in main")
    #import sys
    #sys.exit(1)
    
    test()