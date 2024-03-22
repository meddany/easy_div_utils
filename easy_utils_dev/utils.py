import datetime , string , psutil ,secrets , os ,ping3 , time , sys


def getRandomKey(n=10,numbers=True) :
    if numbers :
        return ''.join(secrets.choice(string.ascii_lowercase + string.digits)
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
    