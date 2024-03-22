# from easy_utils_dev.uiserver import UISERVER
# from time import sleep
# from easy_utils_dev.debugger import DEBUGGER
# from easy_utils_dev.utils import getRandomKey
from easy_utils_dev.ne1830PSS import PSS1830
import time

pss = PSS1830()
jumpserver = pss.nfmtJumpServer('151.98.30.92' , 'root' , 'Nokia@2023')
for i in range(10) :
    time.sleep(1)
    pss = PSS1830(sim=True)
    pss.logger.set_level('debug')
    pss.connect('cli' , '10.198.34.34' , jumpserver=jumpserver )
    pss.get_xcs()
    pss.disconnect()
    
    # 10.198.34.34


# streamer = UISERVER(port=7121)
# streamer.startUi()
# logger = DEBUGGER('testing', stream_service=streamer.socketio) 

# while True :
#     sleep(.25)
#     logger.info(getRandomKey())
    




