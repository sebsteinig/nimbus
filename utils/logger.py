from dataclasses import dataclass
from enum import Enum
import traceback
from datetime import datetime
import os
import sys
from typing import Union
import os.path as path

@dataclass
class Color:
    weight:int
    color:int
    background:int
    def wrap(self,msg)->str:
        if self.background is None:
            return f"\x1b[{self.weight};{self.color}m{msg}\x1b[0m"
        return f"\x1b[{self.weight};{self.color};{self.background}m {msg} \x1b[0m"

class flag(Enum):
    INFO = (Color(1,37,44),Color(1,34,None),"INFO")
    STATUS = (Color(1,37,46),Color(1,36,None),"STATUS")
    SUCCESS = (Color(1,37,42),Color(1,32,None),"SUCCESS")
    FAILURE = (Color(1,37,41),Color(1,31,None),"FAILURE")
    WARNING = (Color(1,37,43),Color(1,33,None),"WARNING")
    DEBUG = (Color(1,37,45),Color(1,35,None),"DEBUG")
    ERROR = (Color(1,37,41),Color(1,31,None),"ERROR")
    def get(self)->str:
        return self.value[0].wrap(self.value[2])
    def blank(self) ->str:
        return self.value[2]
    def tag(self,tag)->str:
        return self.value[1].wrap(tag)
    
def pretty_time_delta(seconds):
    milliseconds = int((seconds - int(seconds))*1000)
    if milliseconds > 0:
        milliseconds = f".{milliseconds}"
    else :
        milliseconds = ""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return f"{days}d{hours}h{minutes}m{seconds}{milliseconds}s"
    elif hours > 0:
        return f"{hours}h{minutes}m{seconds}{milliseconds}s"
    elif minutes > 0:
        return f"{minutes}m{seconds}{milliseconds}s"
    else:
        return f"{seconds}{milliseconds}s"
@dataclass
class _Logger:
    std_output: Union[str , None]
    i = 0
    def debug(self,msg="",tag=None,**var):
        if not Logger._debug:
            return 
        var_display = ""
        if var is not None and len(var) > 0:
            var_display = "\n"
            items = list(var.items())
            for key,value in items[:-1]:
                var_display += f"\t{flag.DEBUG.tag(key)} = {value},\n"
            var_display += f"\t{flag.DEBUG.tag(items[-1][0])} = {items[-1][1]}\n"
        if tag is None :
            self.print(flag.DEBUG,msg + var_display,None)
            return 
        if Logger.is_granted(tag):
            self.print(flag.DEBUG,msg + var_display,tag)
            return
    
    def warning(self,msg,tag=None):
        if not Logger._warning:
            return 
        if tag is None :
            self.print(flag.WARNING,flag.WARNING.value[1].wrap(msg),None)
            return 
        if Logger.is_granted(tag):
            self.print(flag.WARNING,flag.WARNING.value[1].wrap(msg),tag)
            return
    
    def info(self,msg,tag=None):
        if not Logger._info:
            return 
        if tag is None :
            self.print(flag.INFO,flag.INFO.value[1].wrap(msg),None)
            return 
        if Logger.is_granted(tag):
            self.print(flag.INFO,flag.INFO.value[1].wrap(msg),None)
            return
    
    def error(self,msg,tag=None):
        if not Logger._error:
            return 
        if tag is None :
            self.print(flag.ERROR,flag.ERROR.value[1].wrap(msg),None)
            return 
        if Logger.is_granted(tag):
            self.print(flag.ERROR,flag.ERROR.value[1].wrap(msg),tag)
            return
    
    def status(self,msg,sep='',**arg):
        if not Logger._status:
            return 
        items = list(arg.items())
        suffixe = []
        
        for key,value in items[:-1]:
            suffixe.append(flag.STATUS.value[1].wrap(key)+ flag.STATUS.value[1].wrap(' = ')\
                +Color(1,36,47).wrap(value.upper())\
                + flag.STATUS.value[1].wrap(sep))
        suffixe.append(flag.STATUS.value[1].wrap(items[-1][0])+ flag.STATUS.value[1].wrap(' = ')\
                +Color(1,36,47).wrap(items[-1][1].upper()))
        
        print(f"{flag.STATUS.get()} : {flag.STATUS.value[1].wrap(msg)} {''.join(suffixe)}")
    
    def progress_bar(self,var_name,id):
        if Logger._status or Logger._debug:
            return
        loading_sign = [ '-' , '\\' , '|', '/' ,]
        sys.stdout.write(flag.STATUS.tag(f"\r\tNimbus : processing {var_name} for {id} {loading_sign[self.i]}{' '*10}"))
        sys.stdout.flush()
        self.i = (self.i + 1) % 4

    def summary(self,note):
        def wrap(status,msg):
            if status == 0:
                return flag.SUCCESS.tag(msg + " success")
            elif status == 1:
                return flag.WARNING.tag(msg + " skipped")
            else :
                return flag.ERROR.tag(msg + " error")
                
        print()
        print(flag.INFO.tag(f'Summary :\n'))
        for name,((success,total),var_notes) in note.items():
            summary = ""
            print(flag.INFO.tag(f'\t{name} :{success}/{total}\n'))
            for var_name,status in var_notes.items():
                summary += wrap(status,f"\t\t{var_name}") + "\n"
            print(summary)
    
    def success(self,note,time):
        t = pretty_time_delta(time)
        self.summary(note)
        print(f"{flag.SUCCESS.get()} :{flag.SUCCESS.tag(f'conversion to png finished in {t}')}")
    
    def failure(self,note,time):
        t = pretty_time_delta(time)
        self.summary(note)
        print(f"{flag.FAILURE.get()} :{flag.FAILURE.tag(f'conversion to png finished in {t}')}")
           
    def print(self,flag,msg,tag):
        if self.std_output is None:
            print()
            if tag is None:
                print(f"{flag.get()} : {msg}")
            else :
                print(f"{flag.get()} : {flag.tag(tag + ' >>')} {msg}")
            print()
            return
        with open(self.std_output,"a") as file:
            if tag is None:
                file.write(f"{flag.blank()} : {msg}\n")
            else :
                file.write(f"{flag.blank()} : {tag + ' >>'} {msg}\n")
            
    
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
    _status = True
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
    def all(to:bool):
        Logger._debug = to   
        Logger._status = to 
    @staticmethod
    def debug(to:bool):
        Logger._debug = to    
    @staticmethod
    def status(to:bool):
        Logger._status = to    
             
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
    def file(dir:str,variable_name) -> _Logger:
        if not os.path.exists(dir):
            try :
                os.mkdir(dir)
            except:pass
        log_path = path.join(dir,str(variable_name) + datetime.now().strftime("%d_%m_%Y_%H:%M") + ".log")
        return _Logger(log_path)


if __name__ == "__main__":
    print("Cannot execute in main")
    import sys
    sys.exit(1)