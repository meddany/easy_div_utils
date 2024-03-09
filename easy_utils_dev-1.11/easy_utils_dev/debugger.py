import logging , os , inspect
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .utils import getRandomKey
from .custom_env import custom_env , setupEnvironment , insertKey
import json
from .uiserver import UISERVER

def setGlobalHomePath( path ) :
    env = custom_env()
    env['debugger_homepath'] = path
    if not os.path.exists( path ) :
        print(f'Warning: Provided path does not exist. Path is {path}')


class DEBUGGER:
    def __init__(self, name, level='error', onscreen=True,log_rotation=3,homePath=None,id=getRandomKey(9)):
        env = custom_env()
        self.logger = logging.getLogger(name)
        self.set_level(level)
        self.LOG_SIZE_THRESHOLD = 10 * 1024 * 1024
        self.BACKUP_COUNT = log_rotation
        self.homePath = homePath
        self.onScreen= onscreen
        self.id = id
        self.stream_service = None
        self.name = name
        setupEnvironment( 'debugger' )
        env['debugger'][id] = self
        path = self.homepath(homePath)
        # Create a formatter and add it to the handler
        f = f"[%(asctime)s]-[{name}]-[%(levelname)s]: %(message)s"
        formatter = logging.Formatter(f , datefmt='%Y-%m-%d %H:%M:%S' )
        # Create a file handler and set the formatter
        file_handler = RotatingFileHandler(path ,  maxBytes=self.LOG_SIZE_THRESHOLD , backupCount=self.BACKUP_COUNT )
        file_handler.setFormatter(formatter)
        # Add the file handler to the logger
        self.logger.addHandler(file_handler)
        # self.logger.addHandler(self.stream_handler)
        self.logger.addFilter(self.on_log )
        if onscreen : self.enable_print()
        elif not onscreen : self.disable_print()

    def addStreamService( self , socketio , streampath='/debugger/stream/log' ) :
        """
        This function takes a live socketio server. it emit the log message using default path which is /debugger/stream/log
        """
        self.stream_service = socketio
        self.streampath = streampath
        

    def on_log(self , record) :
        if self.stream_service is not None or self.onScreen :
            d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            l = f"[{d}] - [{self.name}] - [{record.levelname}]: {record.getMessage()}"
        if self.stream_service is not None :
            self.stream_service.emit( self.streampath , json.dumps({
                'message' : l ,
                'level' : record.levelname ,
                'msg' : record.getMessage(),
                'date' : d ,
                'id' : self.id
            }))
        if self.onScreen :
            print(l)


    def change_log_size(self, size):
        self.LOG_SIZE_THRESHOLD = size
    

    def homepath(self , path=None ) :
        env = custom_env()
        getFromEnv = env.get('debugger_homepath' , None )
        if getFromEnv is not None :
            self.homePath = getFromEnv
        else :
            if path is not None :
                self.homePath = path
            else :
                self.homePath = os.getcwd()
        if not os.path.exists( self.homePath ) :
            os.makedirs( self.homePath )
        self.homePath = os.path.join( self.homePath, f'{self.name}.log' ) 
        return self.homePath
        


    def enable_print(self) :
        self.onScreen = True

    def disable_print(self) : 
        self.onScreen = False


    def changeHomePath( self , path ) :
        self.homePath = path


    def set_level(self, level : str):
        if 'info' in level.lower() : lvl = logging.INFO
        elif 'warn' in level.lower() : lvl = logging.WARNING
        elif 'warning' in level.lower() : lvl = logging.WARNING
        elif 'critical' in level.lower() : lvl = logging.CRITICAL
        elif 'debug' in level.lower() : lvl = logging.DEBUG
        elif 'error' in level.lower() : lvl = logging.ERROR
        self.logger.setLevel(lvl)

    def get_logger(self) : 
        return self.logger

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
