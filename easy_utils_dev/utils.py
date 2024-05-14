import datetime , string , psutil ,secrets , os ,ping3 , time , sys


def getRandomKey(n=10,numbers=True) :
    if numbers :
        return ''.join(secrets.choice(string.digits)
            for i in range(n))
    else :
        return ''.join(secrets.choice(string.ascii_lowercase )
            for i in range(n))


def now() :
    return datetime.datetime.now()

def date_time_now() :
    return  str( now().replace(microsecond=0))


def timenow() : 
    return  str(now().strftime("%d/%m/%Y %H:%M:%S"))
    

def timenowForLabels() : 
    return now().strftime("%d-%m-%Y_%H-%M-%S")


def getDateTimeAfterFewSeconds(seconds=10):
    import datetime
    # Get the current time
    current_time = datetime.datetime.now()
    # Add the specified number of seconds
    new_time = current_time + datetime.timedelta(seconds=seconds)
    # Format the new time as a string
    return new_time.strftime('%Y-%m-%d %H:%M')


def isOsPortFree(port : str):
    for conn in psutil.net_connections():
        if str(conn.laddr.port) == port :
            return False
    return True

def generateToken(iter=5) :
    return '-'.join( [ getRandomKey(n=5) for x in range( iter )] )


def pingAddress( address ) : 
    response  = ping3.ping(f'{address}')
    if response == None or response == False :
        return False
    else :
        return True

def getScriptDir(f= __file__):
    '''
    THis functions aims to return the script dir even if app is bundeled with py installer.
    '''
    if getattr(sys, 'frozen', False): 
        # The script is run from a bundled exe via PyInstaller
        path = sys._MEIPASS 
    else:
        # The script is run as a standard script
        path = os.path.dirname(os.path.abspath(f))
    return path

def getScriptDirInMachine(f= __file__):
    '''
    THis functions aims to return the script dir.
    '''
    return os.path.dirname(os.path.abspath(f))



def is_packed():
    # Check if the script is running from an executable produced by PyInstaller
    if getattr(sys, 'frozen', False):
        return True
    # Check if the 'bundle' directory exists
    elif hasattr(sys, '_MEIPASS') and os.path.exists(os.path.join(sys._MEIPASS, 'bundle')):
        return True
    else:
        return False

def get_executable_path(file=__file__) :
    if is_packed():
        return os.path.dirname(os.path.realpath(sys.argv[0]))
    return os.path.dirname(os.path.realpath(file))

def isArgsEmpty(args) :
    if True in args.__dict__.values() :
        return False
    else :
        return True
    
def convert_bytes_to_mb(bytes_size,rounded=True):
    """Convert bytes to megabytes (MB)."""
    if rounded :
        # print(f'''
        # {bytes_size} =>>> {round(float(bytes_size))}
        # ''')
        return round(float(bytes_size / (1024 * 1024)))
    return bytes_size / (1024 * 1024)

def convert_bytes_to_kb(bytes_size,rounded=True):
    """Convert bytes to kilobytes (KB)."""
    if rounded :
        return round(float(bytes_size / 1024))
    return bytes_size / 1024

def convert_mb_to_bytes(mb_size):
    return mb_size * 1024 * 1024

def getTimestamp(after_seconds=None) :
    '''
    get timestamp now or after few seconds.
    after_seconds is int.
    '''
    if not after_seconds :
        return int(time.time())
    return int(time.time()) + int(after_seconds)


if __name__ == "__main__":
    pass
