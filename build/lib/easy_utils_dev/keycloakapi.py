
from easy_utils_dev.debugger import DEBUGGER
import requests , json , subprocess , time
import urllib3
from threading import Thread
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

version = '1.0 build 22032024'

class KeyCloack :
    def __init__(self, address,  user, password,port=8443 ,debug_name='keycloackapi', token_refresh_period=1700, client_id='wp-lra-service',client_secret='c74b4dfb-4293-46da-a38a-9fd46fce23b0') -> None:
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
        self.client_secret=client_secret
        self.baseUrl = self.updateBaseUrl(address , port )
        self.sessions = {}

    def set_debug_level(self , level ) :
        self.logger.set_level(level)    

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
        self.logger.info('Starting to authenticate with KeyCloack platform ..')
        url = f'{self.baseUrl}/wavesuite/common/auth/realms/wavesuite/protocol/openid-connect/token'
        self.logger.info(f"Authentication Params: username={self.username} password=********")
        self.logger.debug(f"Authentication Params: username={self.username} password={self.password} url={url}")
        payload = {
            'grant_type': 'client_credentials',
            'username': self.username ,
            'password': self.password,
            'client_id': self.client_id ,
            'client_secret': self.client_secret
        }
        headers = {'Content-type': 'application/x-www-form-urlencoded' }
        self.logger.debug(f'Authentication Payload: {payload}')
        response = requests.post(url , data=payload , headers=headers , verify=False)
        self.logger.info(f'Authentication response code={response.status_code}')
        self.logger.debug(f'raw response in authentication {response.text}')
        if response.status_code != 200 :
            self.logger.error(f'Authentication failed. status_code={response.status_code} {response.text}')
            raise Exception(f'Authentication Failure {response.status_code}')
        response = response.json()
        self.accessToken = response['access_token']
        self.bearertoken = f"Bearer {self.accessToken}"
        if autoRefresh :
            self.logger.debug(f'auto refresh is enabled. starting auto refresh thread ..')
            t = Thread( target=self.autoRefreshToken )
            t.start()
        self.logger.debug(f'returning access token {self.accessToken}')
        return self.accessToken
        
    def getAccessToken(self) :
        return self.accessToken
    
    def getRefreshToken(self) :
        return self.accessToken
    
    def getBearerToken(self) :
        return self.bearertoken

    def getAuthorizationToken(self) :
        return self.getBearerToken()

    def getHeaders( self , headers={}, json=True ) :
        _h = {'Authorization' : self.getBearerToken() }
        self.logger.debug(f'request headers is {_h}')
        if json :
            self.logger.debug(f"json content type is Enabled. adding Content-type as application/json ")
            _h.update({'Content-type': 'application/json'})
        _h.update(headers)
        return _h

    def logout(self,userId) :
        self.logger.info('Starting to logout form KeyCloack platform ..')
        url = f'{self.baseUrl}/admin/realms/heroes/users/{userId}/logout'
        self.logger.info(f"Authentication Params: username={self.username}.")
        payload = {'refreshToken' : self.accessToken }
        headers = self.getHeaders()
        self.logger.debug(f'Logout out headers {headers}')
        self.logger.debug(f'Logout out payload {payload}')
        response = requests.post(url , data=json.dumps(payload) , headers=headers , verify=False)
        self.logger.debug(f'raw response in logout {response.text}')
        self.logger.info(f'Logout status code={response.status_code}')

    def getUsers(self) :
        self.logger.info(f"Get users from KeyCloack ...")
        url= f"{self.baseUrl}/wavesuite/common/auth/admin/realms/wavesuite/users/"
        headers = self.getHeaders()
        self.logger.debug(f'Get users headers = {headers}')
        response = requests.get(url , headers=headers , verify=False)
        self.logger.info(f'Get Usr response code={response.status_code}')
        self.logger.debug(f'raw response in authentication {response.text}')
        if response.status_code == 200 :
            self.logger.debug(f'response is 200 , return the json as dict and filter on data ...')
            self.users = response.json()
            return self.users
        else :
            self.logger.error(f'Error getting users  {response.text}')
            self.logger.debug(f'response is not 200 , return empty array')
            self.users = []
            return []
        

    def updateUser(self , user ) :
        userId=user.get('id')
        username=user.get('username')
        self.logger.info(f"Update user in KeyCloack for userId={userId} username={username}")
        url= f"{self.baseUrl}/wavesuite/common/auth/admin/realms/wavesuite/users/{userId}"
        headers = self.getHeaders()
        self.logger.debug(f'update user headers = {headers}')
        self.logger.debug(f'data user payload = {user}')
        response = requests.put(url , headers=headers, data=json.dumps(user) , verify=False)
        self.logger.info(f'update Usr response code={response.status_code}')
        self.logger.debug(f'raw response in user update {response.text}')
        if response.status_code == 204 :
            self.logger.debug(f'response is 204 , return True as status...')
            return True
        else :
            self.logger.error(f'Error getting users  {response.text}')
            self.logger.debug(f'response is not 204. return False error={response.text}')
            return False
        
if __name__ == '__main__':
    pass



