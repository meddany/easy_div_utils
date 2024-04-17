
from easy_utils_dev.debugger import DEBUGGER
import requests , json , subprocess , time
import urllib3
from threading import Thread
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from easy_utils_dev.cplib import *

version = '1.0 build 22032024'

class LraLib :
    def __init__(self, address,  user, password,port=8443 ,debug_name='lralib', token_refresh_period=1700 , client_id='wp-lra-service',client_secret='c74b4dfb-4293-46da-a38a-9fd46fce23b0' ) -> None:
        '''
        address: string
        token_refresh_period number , string
        password : string
        port : int
        debug_name : string
        '''
        self.logger = DEBUGGER(debug_name)
        self.address = address
        self.port = port
        self.baseUrl = f'https://{self.address}:{self.port}'
        self.username = user
        self.password = password
        self.users = []
        self.autoRefreshTokenPeriod = token_refresh_period
        self.client_id=client_id
        self.client_secret = client_secret
        self.baseUrl = self.updateBaseUrl(address , port )
        self.debug=False

    def set_debug_level(self , level ) :
        self.logger.set_level(level) 
        self.debug = True

    def updateBaseUrl( self, address, port ) :
            self.baseUrl = f"https://{address}:{port}"
            self.logger.debug(f'baseUrl={self.baseUrl}')
            self.address = address
            self.port = port
            return self.baseUrl

    def disableOnScreenDebugPrint( self ) :
        self.logger.disable_print()
    
    
    def enableOnScreenDebugPrint( self ) :
        self.logger.enable_print()

    def autoRefreshToken(self) :
        self.logger.info(f'Auto refresh token started. waiting for {self.autoRefreshTokenPeriod} refresh ...')
        time.sleep(self.autoRefreshTokenPeriod )
        self.logout()
        self.authentication()
        self.logger.info(f'Auto Token refresh completed.')


    def authentication(self,autoRefresh=True) :
        self.logger.info('Starting to authenticate with LRA platform ..')
        # url = f'{self.baseUrl}/wavesuite/common/auth/realms/wavesuite/protocol/openid-connect/token'
        # self.logger.info(f"Authentication Params: username={self.username} password=********")
        # self.logger.debug(f"Authentication Params: username={self.username} password={self.password} url={url}")
        # payload = {
        #     'grant_type': 'password',
        #     'username': self.username ,
        #     'password': self.password,
        #     'client_id': self.client_id,
        #     'client_secret': self.client_secret
        # }
        # headers = {'Content-type': 'application/x-www-form-urlencoded' }
        # self.logger.debug(f'Authentication Payload: {payload}')
        # response = requests.post(url , data=payload , headers=headers , verify=False)
        # self.logger.info(f'Authentication response code={response.status_code}')
        # self.logger.debug(f'raw response in authentication {response.text}')
        # if response.status_code != 200 :
        #     self.logger.error(f'Authentication failed. status_code={response.status_code} {response.text}')
        #     raise Exception(f'Authentication Failure {response.status_code}')
        # response = response.json()
        # self.accessToken = response['access_token']
        # self.refreshToken = response['refresh_token']
        # if autoRefresh :
        #     self.logger.debug(f'auto refresh is enabled. starting auto refresh thread ..')
        #     t = Thread( target=self.autoRefreshToken )
        #     t.start()
        # self.logger.debug(f'returning access token {self.accessToken}')
        self.cp = cp = CommonPlatformLib(
            address=self.address,
            port=self.port,
            username=self.username,
            password=self.password,
            token_refresh_period=self.autoRefreshTokenPeriod,
        )
        if self.debug :
            cp.logger.set_level('debug')
        cp.authentication(autoRefresh=autoRefresh)
        self.accessToken = cp.accessToken
        self.refreshToken = cp.refreshToken
        self.logger.info('Authenticate with LRA platform Completed')
        return cp.accessToken
        
    def getAccessToken(self) :
        return self.accessToken
    
    def getRefreshToken(self) :
        return self.accessToken
    
    def getBearerToken(self) :
        return f"Bearer {self.accessToken}"

    def getAuthorizationToken(self) :
        return self.getBearerToken()

    def getHeaders( self , headers={}, json=True ) :
        _h = {'Authorization' : f"Bearer {self.accessToken}"}
        self.logger.debug(f'request headers is {_h}')
        if json :
            self.logger.debug(f"json content type is Enabled. adding Content-type as application/json ")
            _h.update({'Content-type': 'application/json'})
        _h.update(headers)
        return _h

    def logout(self) :
        self.logger.info('Starting to logout form LRA platform ..')
        self.cp.logout()
        self.logger.info('Logout form LRA platform Completed')

    def getUsers(self) :
        self.logger.info(f"Get users from LRA ...")
        url= f"{self.baseUrl}/lra-rest/users"
        headers = self.getHeaders()
        self.logger.debug(f'Get users headers = {headers}')
        response = requests.get(url , headers=headers , verify=False)
        self.logger.info(f'Get Usr response code={response.status_code}')
        self.logger.debug(f'raw response in authentication {response.text}')
        if response.status_code == 200 :
            self.logger.debug(f'response is 200 , return the json as dict and filter on data ...')
            self.users = response.json().get('items')
            return self.users
        else :
            self.logger.error(f'Error getting users  {response.text}')
            self.logger.debug(f'response is not 200 , return empty array')
            self.users = []
            return []

    def createUser(self, user : dict , group ) :
        username = user.get('userName')
        self.logger.info(f'Starting to create {username}  with group {group} ...')
        url= f"{self.baseUrl}/lra-rest/users"
        self.logger.debug(f'creating user {username} using url {url} with POST')
        if group == 'ROLE_ADMIN' :
            lra_operatorRole = False 
            adminRole  = True 
            lra_viewerRole = False
        elif group == 'ROLE_LRA_OPERATOR' :
            lra_operatorRole = True 
            adminRole  = False 
            lra_viewerRole = False
        elif group == 'ROLE_LRA_VIEWER' :
            lra_operatorRole = False 
            adminRole  = False 
            lra_viewerRole = True
        payload = {
            'address' : '' ,
            'adminRole' : adminRole ,
            'contact' : '' ,
            'email' : user.get('email') ,
            'enabled' : True  ,
            'disabled' : False ,
            'localUser' : False , 
            'loginAttemptLocked' : False,
            'lra_operatorRole' : lra_operatorRole , 
            'lra_viewerRole' : lra_viewerRole , 
            'name' : username ,
            'phoneNumber' : '' ,
            'roles' : [group] ,
            'userSource' : False,
            'username' : user.get('email') # yes this must be email.    
        }
        self.logger.debug(f'Creating {username} using form {payload}')
        headers = self.getHeaders()
        response = requests.post(url , data=json.dumps(payload) , headers=headers , verify=False)
        self.logger.debug(f'raw response {response.text}')
        self.logger.info(f'create user {username} status code={response.status_code}')
        return response


if __name__ == '__main__':
    pass



