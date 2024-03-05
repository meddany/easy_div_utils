import os 

'''
in custom env. you can setup custom environment and store any object. not like normal env...
which can store only strings.
'''

class CustomDict(dict):
    def __init__(self, *args, **kwargs):
        # Set up default keys and values
        self.default_values = {}
        
        # Update the defaults with the provided arguments
        self.default_values.update(dict(*args, **kwargs))
        
        # Call the __init__ method of the base class (dict) with the updated defaults
        super().__init__(self.default_values)
        

# define the global environment dict.
env = cenv = _custom_env = CustomDict()


def enject_osEnv() :
    global _custom_env
    _custom_env.update(os.environ.items())

def custom_env():
    return _custom_env


def clear_env( clear_os_env=True ) :
    global _custom_env
    
    if clear_os_env :
        _custom_env = CustomDict()

    else :
        for key , _ in _custom_env.items():
            if not key in list(os.environ.keys()) :
                del _custom_env[key]
        
def getKey(key) :
    return _custom_env.get(key , None)

def insertKey( key , value ) :
    _custom_env[key] = value

def setupEnvironment( key:str ) :
    '''
    This function will create a new dict inside the global environment if the environment was not already created.

    @Parameters key : string
    '''
    if not _custom_env.get( key , None ):
        _custom_env[key] = {}


if __name__ == '__main__':
    pass
