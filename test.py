from easy_utils_dev.uiserver import UISERVER
from time import sleep
from easy_utils_dev.debugger import DEBUGGER
from easy_utils_dev.utils import getRandomKey

streamer = UISERVER(port=7121)
streamer.startUi()
logger = DEBUGGER('testing', stream_service=streamer.socketio) 

while True :
    sleep(.25)
    logger.info(getRandomKey())
    



