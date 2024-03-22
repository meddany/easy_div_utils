from easy_utils_dev.debugger import DEBUGGER
import requests , json
from requests.auth import HTTPBasicAuth as BAuth
from easy_utils_dev.utils import pingAddress
from time import sleep
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from threading import Thread

class WSNOCLIB : 
    def __init__(self, ip , username , password ,debug_level='info'): 
        self.logger = DEBUGGER('wsnoclib',level=debug_level)
        self.disabledWarnings = self.disableUrlWarnings()
        self.address = ip
        self.username = username
        self.password = password
        self.baseUrl = self.createBaseUrl()

    def supress_logs(self) :
        self.logger.disable_print()

    def createBaseUrl(self) :
        self.baseUrl = f'https://{self.address}'
        return self.baseUrl

    def change_debug_level(self , level) :
        if not level in ['info' , 'error' , 'debug' , 'warn'] :
            raise Exception(f"Not valid debugging level: {level}. Levels {['info' , 'error' , 'debug' , 'warn']}")
        self.logger.set_level(level)

    def disableUrlWarnings(self) :
        disable_warnings(InsecureRequestWarning)
        return True


    def connect(self,auto_refresh_token=True) : 
        if not pingAddress(self.address) :
            raise Exception(f'Address {self.address} is not pingable.')
        self.logger.info(f'Connecting to {self.address} using username: {self.username} ...')
        r = requests.post(url = f"https://{self.address}/rest-gateway/rest/api/v1/auth/token", auth=BAuth(self.username, self.password), verify=False, json={"grant_type": "client_credentials"})
        self.logger.info(f'Request return status code : {r.status_code}')
        if r.status_code != 200 :
            raise Exception(f'Failed to authenticate WSNOC. Return status code : {r.status_code}')
        self.access_token = r.json()["access_token"]
        self.refresh_token = r.json()["refresh_token"]
        self.bearer_token = f'Bearer {self.access_token}'
        self.token = r.json()
        self.token.update({'bearer_token' :  self.bearer_token })
        if auto_refresh_token :
            self.autoRefreshThread = Thread(target=self.runAutoRefreshThread).start()
        self.logger.debug(f'token=> {r.text}')
        return self.token


    def getLatestToken(self) :
        return self.token


    def logout(self) :
        self.logger.info(f"Logging out from {self.address} ...")
        body = f"token={self.access_token}&token_type_hint=token"
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(url = f"https://{self.address}/rest-gateway/rest/api/v1/auth/revocation",
                         auth=BAuth(self.username, self.password),verify=False,data=body,headers=header)
        self.logger.info(f"Logging out from {self.address}, response code={r.status_code}")
        if r.status_code != 200 :
            self.logger.error(f"Failed logging out from {self.address}")

    def runAutoRefreshThread(self) : 
        self.logger.info('Waiting for auto refresh in 2700sec, 45min ...')
        sleep(2700)
        self.logout()
        self.connect(self.address , self.username , self.password)


    def get(self, url , port=8443 , return_json=True ) :
        if not str(url).startswith('/') :
            url = f"/{url}"
        if port is None :
            url = f"{self.baseUrl}{url}"
        else :
            url = f"{self.baseUrl}:{port}{url}"
        self.logger.info(f'request [GET] : {url}')
        headers={ 'Authorization' : self.bearer_token }
        r = requests.get(url , headers=headers , verify=False )
        self.logger.info(f'request [GET] : {url} [{r.status_code}]')
        self.logger.debug(f'response {url} : {r.text}')
        if r.status_code != 200 :
            self.logger.error(f'request [GET]: {url} status code: {r.status_code}')
        if return_json :
            return r.json()
        return r

    def post(self, url , port=8443 , body={} , headers={} , return_json=False ) :
        if not str(url).startswith('/') :
            url = f"/{url}"
        if port is None :
            url = f"{self.baseUrl}{url}"
        else :
            url = f"{self.baseUrl}:{port}{url}"
        self.logger.info(f'request [POST] : {url}')
        _headers={ 'Authorization' : self.bearer_token }
        headers.update(_headers)
        r = requests.post( url , headers=headers , data=body , verify=False )
        self.logger.info(f'request [POST] : {url} [{r.status_code}]')
        self.logger.debug(f'response {url} : {r.text}')
        if r.status_code != 200 :
            self.logger.error(f'request [POST]: {url} status code: {r.status_code}')
        if return_json :
            return r.json()
        return r
    

    def session_info(self) :
        self.logger.info('Getting Version ...')
        response = self.get( url='/oms1350/data/common/sessionInfo')
        return response

    def get_nodes(self) :
        self.logger.info(f"Requesting Nodes ..")
        response = self.get( url="/oms1350/data/npr/nodes" )
        return response

    def get_nes(self) :
        self.logger.info(f"Requesting Network Elements ..")
        response = self.get( url="/oms1350/data/npr/nes")
        return response

    def get_version(self) :
        self.logger.info(f"Getting Version ...")
        response = self.get('/oms1350/data/otn/system/getVersion')
        return response

    def fullSync(self , nodeId, nodeName ) :
        self.logger.info(f'Trigger Full Sync for node %s' % nodeId)
        url = f'/oms1350/data/npr/nodes/{nodeId}'
        headers={"Content-Type" : "application/json" , "Accept" : "application/json" }
        body= json.dumps({"Tag":"F_POP_neFullSyncro","userLabel": nodeName })
        response=self.post( url=url , body=body , headers=headers ,return_json=False )
        return response.json()

if __name__ == '__main__' :
    noc = WSNOCLIB('135.183.142.226' , 'admin' , 'Nokia@2023') 
    noc.connect(auto_refresh_token=False)
    noc.fullSync(nodeName='Site-4' , nodeId=7)
    noc.logout()
