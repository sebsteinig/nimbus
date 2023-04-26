from dataclasses import dataclass
from enum import Enum
from io import TextIOWrapper
import traceback
from datetime import datetime
import os
from typing import Union
from file_managers.default_manager import FileManager
from file_managers.bridge.bridge_manager import BridgeManager
import os.path as path
@dataclass
class _Logger:
    std_output: Union[str , None]
    def debug(self,msg,tag=None):
        if not Logger._debug:
            return 
        if tag is None :
            self.print(f"DEBUG : {msg}")
            return 
        if Logger.is_granted(tag):
            self.print(f"DEBUG : {tag} >> {msg}")
            return
    
    def warning(self,msg,tag=None):
        if not Logger._warning:
            return 
        if tag is None :
            self.print(f"WARNING : {msg}")
            return 
        if Logger.is_granted(tag):
            self.print(f"WARNING : {tag} >> {msg}")
            return
    
    def info(self,msg,tag=None):
        if not Logger._info:
            return 
        if tag is None :
            self.print(f"INFO : {msg}")
            return 
        if Logger.is_granted(tag):
            self.print(f"INFO : {tag} >> {msg}")
            return
    
    def error(self,msg,tag=None):
        if not Logger._error:
            return 
        if tag is None :
            self.print(f"ERROR : {msg}")
            return 
        if Logger.is_granted(tag):
            self.print(f"ERROR : {tag} >> {msg}")
            return
    
    
    def print(self,msg):
        if self.std_output is None:
            print(msg)
            return
        with open(self.std_output,"a") as file:
            file.write(msg + "\n")
    
class LoggerMode(Enum):
    BLACK_LIST = 1
    WHITE_LIST = 2

class Logger:    
    mode = LoggerMode.BLACK_LIST
    filters = []
    _debug = True
    _warning = True
    _info = True
    _error = True
    _console : _Logger = _Logger(None)
    @staticmethod   
    def filter(*arg):
        Logger.filters.extend(arg)
    
    @staticmethod
    def blacklist():
        Logger.mode = LoggerMode.BLACK_LIST
    
    @staticmethod
    def whitelist():
        Logger.mode = LoggerMode.WHITE_LIST
       
    @staticmethod
    def debug(to:bool):
        Logger._debug = to    
             
    @staticmethod
    def warning(to:bool):
        Logger._warning = to    
              
    @staticmethod
    def info(to:bool):
        Logger._info = to    
                  
    @staticmethod
    def error(to:bool):
        Logger._error = to    
         
    @staticmethod
    def is_granted(tag) -> bool:
        return (Logger.mode is LoggerMode.BLACK_LIST and not tag in Logger.filters) or (Logger.mode is LoggerMode.WHITE_LIST and  tag in Logger.filters)
                      
    @staticmethod
    def trace() -> str:
        return traceback.format_exc()
    
    @staticmethod
    def console() -> _Logger:
        return Logger._console
    
    @staticmethod
    def file(file_manager: Union[FileManager , BridgeManager],input,variable_name) -> _Logger:
        out_folder = file_manager.get_output(input)
        log_path = path.join(out_folder.out(),str(variable_name) + datetime.now().strftime("%d_%m_%Y_%H:%M") + ".log")
        
        return _Logger(log_path)


if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)