import traceback
from datetime import datetime
import os

def logErrorForAll(err):
    logFile = open(datetime.now().strftime("%d%m%Y_%H:%M:%S") + ".log", "a")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n\n\n\n{err.args[0]}")
    logFile.close()

def logErrorForVarAndExpid(variable, expid, err):
    logFile = open(os.path.join("out", expid.name, f"{expid.name}{variable.variable.name}{datetime.now().strftime('%d%m%Y_%H:%M:%S')}.log"), "a")
    logFile.write(f"-------------error when converting experience : {expid.name} with variable : {variable.variable.name}---------------\n")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n : {err.args[0]}")
    logFile.close()

def logErrorForVar(variable, err):
    logFile = open(os.path.join("out", f"{variable.variable.name}{datetime.now().strftime('%d%m%Y_%H:%M:%S')}.log"), "a")
    logFile.write(f"-------------error when converting with variable : {variable.variable.name}---------------\n")
    traceback.print_tb(err.__traceback__, file=logFile)
    logFile.write(f"\n : {err.args[0]}")
    logFile.close()

    
if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)