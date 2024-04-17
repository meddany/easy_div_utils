import logging , os 
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .utils import getRandomKey,  convert_bytes_to_mb , convert_mb_to_bytes 
from .custom_env import custom_env , setupEnvironment
import json 
from .Events import EventEmitter

def setGlobalHomePath( path ) :
    env = custom_env()
    env['debugger_homepath'] = path
    if not os.path.exists( path ) :
        print(f'Warning: Provided path does not exist. Path is {path}')

def setGlobalDisableOnScreen(on_screen=False) :
    env = custom_env()
    env['debugger_on_screen'] = on_screen
    
def setGlobalDebugLevel(level='info') :
    env = custom_env()
    env['debugger_global_level'] = level


class DEBUGGER:
    def __init__(self, name, level='info', onscreen=True,log_rotation=3,homePath=None,id=getRandomKey(9) , global_debugger=None,disable_log_write=False):
        env = custom_env()
        env['debugger_on_screen'] = True
        self.env = env
        self.events = EventEmitter()
        self.logger = logging.getLogger(name)
        self.set_level(level)
        self.LOG_SIZE_THRESHOLD_IN_BYTES = 10 * 1024 * 1024
        self.BACKUP_COUNT = log_rotation
        self.homePath = homePath
        self.onScreen= onscreen
        self.id = id
        self.how_many_times_write= 0
        self.stream_service = None
        self.name = name
        self.rotate_disabled=False
        self.log_iterations=0
        self.log_iterations_threshold = 200
        self.global_debugger = global_debugger
        self.type = "CUSTOM_DEBUGGER"
        setupEnvironment( 'debugger' )
        env['debugger'][id] = self
        f = f"[%(asctime)s]-[{name}]-[%(levelname)s]: %(message)s"
        self.formatter = logging.Formatter(f , datefmt='%Y-%m-%d %H:%M:%S' )
        path = self.homepath(homePath)
        self.file_handler_class = None
        self.file_handler_class = self.createRotateFileHandler(path)
        self.logger.addFilter(self.on_log )
        self._disable_log_write = disable_log_write
        if onscreen : self.enable_print()
        elif not onscreen : self.disable_print()

    def advertiseGlobalDebugLevel(self , level) :
        setGlobalDebugLevel(level)

    def disable_rotate(self) :
        self.rotate_disabled = True

    def enable_rotate(self) :
        self.rotate_disabled = False

    def createRotateFileHandler( self , path ) :
        old = self.file_handler_class 
        if old :
            self.logger.removeHandler(old)
        file_handler = RotatingFileHandler(path ,  maxBytes=self.LOG_SIZE_THRESHOLD_IN_BYTES , backupCount=self.BACKUP_COUNT )
        self.file_handler= file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        return file_handler

    def update_log_iterantions_threshold(self,threshold : int ):
        '''
        set value when rotation should be checked. when every on_log function called.
        by default rotation will be checked every 200 on_log function call.
        '''
        self.log_iterations_threshold = threshold

    def updateGlobalDebugger(self , logger ) :
        '''
        this function pass the log message to other logger to write the same log message to it.
        logger must be debugger class.
        '''
        if logger.type != 'CUSTOM_DEBUGGER' :
            raise Exception(f'Invalid logger type. must pass debugger class.')
        self.global_debugger = logger


    def getStreamServiceUrlPath(self) :
        return self.streampath

    def getStreamService(self) :
        return self.stream_service

    def isStreamServiceAvailable(self) :
        if self.stream_service :
            return True
        return False

    def addStreamService( self , socketio , streampath='/debugger/stream/log' ) :
        """
        This function takes a live socketio server. it emit the log message using default path which is /debugger/stream/log
        """
        self.stream_service = socketio
        self.streampath = streampath
        
    def updateLogName( self , name ) :
        self.name = name

    def disable_log_write(self) :
        '''
        this function is used to disable the log write to file. if onScreen is enabled, logs will be displayed only on screen.
        '''
        self._disable_log_write = True

    def manage_file_rotation(self, record ) :
        handler = self.get_rotate_handler()
        if handler.shouldRollover(record) :
            handler.doRollover()
            self.log_iterations = 0

    def on_log(self , record) :
        if not self._disable_log_write and not self.stream_service and not self.onScreen and not self.env['debugger_on_screen'] :
            return
        if self.rotate_disabled :
            if self.log_iterations > self.log_iterations_threshold:
                self.manage_file_rotation(record)
            else :
                self.log_iterations += 1
        d = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        l = f"[{d}] - [{self.name}] - [{record.levelname}]: {record.getMessage()}"
        if self.env.get('debugger_global_level' , None) : 
            self.set_level( level=self.env.get('debugger_global_level') )
        if not self._disable_log_write :
            with open(self.homePath , 'a+') as f :
                f.write(f"{l}\n")
        if self.isStreamServiceAvailable() :
            self.stream_service.emit( self.getStreamServiceUrlPath() , json.dumps({
                'message' : l ,
                'level' : record.levelname ,
                'msg' : record.getMessage(),
                'date' : d ,
                'id' : self.id,
                'formate' : 'json'
            }))
        if self.onScreen and self.env['debugger_on_screen'] == True :
            print(l)

    def get_rotate_handler(self) :
        return self.file_handler_class
            
    def change_log_size(self, size) -> bool:
        '''
        change the size of each log file rotation.
        default is 10M
        size should be passed as MB
        '''
        print(f"LOG SIZE CHANGE FROM {convert_bytes_to_mb(self.LOG_SIZE_THRESHOLD_IN_BYTES)} to {size} MB")
        size = convert_mb_to_bytes(size)
        self.LOG_SIZE_THRESHOLD_IN_BYTES = size
        handler = self.get_rotate_handler()
        handler.maxBytes = size
        return True

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
        p = self.homepath(path)
        self.file_handler_class = self.createRotateFileHandler(p)

    def isGlobalDebuggerDefined(self) :
        if self.global_debugger :
            return True
        else :
            return False

    def set_level(self, level : str):
        if 'info' in level.lower() : lvl = logging.INFO
        elif 'warn' in level.lower() : lvl = logging.WARNING
        elif 'warning' in level.lower() : lvl = logging.WARNING
        elif 'critical' in level.lower() : lvl = logging.CRITICAL
        elif 'debug' in level.lower() : lvl = logging.DEBUG
        elif 'error' in level.lower() : lvl = logging.ERROR
        else : raise ValueError('Unknown level, not one of [info,warn,warning,critical,debug,error]')
        self.logger.setLevel(lvl)

    def get_logger(self) : 
        return self.logger

    def info(self, message):
        self.logger.info(message)
        if self.isGlobalDebuggerDefined() : 
            self.global_debugger.info(message)

    def debug(self, message):
        self.logger.debug(message)
        if self.isGlobalDebuggerDefined() : 
            self.global_debugger.debug(message)

    def warning(self, message):
        self.logger.warning(message)
        if self.isGlobalDebuggerDefined() : 
            self.global_debugger.warning(message)

    def error(self, message):
        self.logger.error(message)
        if self.isGlobalDebuggerDefined() : 
            self.global_debugger.error(message)

    def critical(self, message):
        self.logger.critical(message)
        if self.isGlobalDebuggerDefined() : 
            self.global_debugger.critical(message)