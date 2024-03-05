import logging , os , inspect
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .utils import getRandomKey
from .custom_env import custom_env , setupEnvironment , insertKey



def setGlobalHomePath( path ) :
    env = custom_env()
    env['debugger_homepath'] = path
    if not os.path.exists( path ) :
        print(f'Warning: Provided path does not exist. Path is {path}')


class DEBUGGER:
    def __init__(self, name, level='info', onscreen=True,log_rotation=3,homePath=None,id=getRandomKey(9) ):
        env = custom_env()
        self.logger = logging.getLogger(name)
        self.set_level(level)
        self.LOG_SIZE_THRESHOLD = 10 * 1024 * 1024
        self.BACKUP_COUNT = log_rotation
        self.homePath = homePath
        self.id = id
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


        # Create a stream handler and set the formatter
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(self.stream_handler)

        if onscreen : self.enable_print()
        elif not onscreen : self.disable_print()


    def callback( original_function ) :
        def wrapper(*args, **kwargs):
            result = original_function(*args, **kwargs)
            print(f"Function '{original_function.__name__}' has finished running.")

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
        self.logger.addHandler(self.stream_handler)

    def disable_print(self) : 
         self.logger.removeHandler(self.stream_handler)


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


    def get_current_function(self):
        frame = inspect.currentframe().f_back.f_back
        function_name = frame.f_code.co_name
        # print(function_name)
        return function_name
    
