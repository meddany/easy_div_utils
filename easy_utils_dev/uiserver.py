from werkzeug.serving import ThreadedWSGIServer
from easy_utils_dev.utils import getRandomKey , generateToken
from flask_socketio import SocketIO
from engineio.async_drivers import gevent
from engineio.async_drivers import threading
from flask_cors import CORS
import logging ,  json
from flask import Flask , send_file
from threading import Thread
from easy_utils_dev.custom_env import cenv


def getClassById( id ) :
    return cenv[id]

class UISERVER :
    def __init__(self ,id=getRandomKey(n=15),secretkey=generateToken(),address='localhost',port=5312,**kwargs) -> None:
        self.id = id
        self.app = app = Flask(self.id)
        app.config['SECRET_KEY'] = secretkey
        CORS(app,resources={r"/*":{"origins":"*"}})
        self.address= address 
        self.port = port
        self.socketio = SocketIO(app , cors_allowed_origins="*"  ,async_mode='threading' , engineio_logger=False , always_connect=True ,**kwargs )
        cenv[id] = self
        self.fullAddress = f"http://{self.address}:{self.port}"

    def getInstance(self) :
        return self.getFlask() , self.getSocketio() , self.getWsgi()
    
    def getSocketio( self ):
        return self.socketio
    
    def getFlask( self ):
        return self.app
    
    def getWsgi(self) :
        return self.wsgi_server

    def shutdownUi(self) :
        self.wsgi_server.shutdown()

    def startUi(self) :

        @self.app.route('/connection/test/internal' , methods=['GET'])
        def test_connection():
            return json.dumps({'status' : 200 , 'id' : self.id })

        self.wsgi_server = wsgi_server = ThreadedWSGIServer(
            host = self.address ,
            port = self.port,
            app = self.app )
        
        def _start() :
            print(f"web-socket: {self.fullAddress}")
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            wsgi_server.serve_forever()   


        
        self.flaskprocess = Thread(target=_start)
        self.flaskprocess.daemon = True
        self.flaskprocess.start()