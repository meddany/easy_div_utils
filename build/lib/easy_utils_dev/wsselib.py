
from easy_utils_dev.debugger import DEBUGGER
import requests , json , subprocess , time
import urllib3
from threading import Thread
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

version = '1.0 build 22032024'

class SeLib :
    def __init__(self, address,  user, password, tenantId,port=28443 ,debug_name='wsselib', token_refresh_period=30) -> None:
        self.logger = DEBUGGER(debug_name)
        self.address = address
        self.port = port
        self.baseUrl = f"https://{self.address}:{self.port}/wavesuite/se/api"
        self.seUsername = user
        self.sePassword = password
        self.tenantId = tenantId
        self.users = []
        self.autoRefreshTokenPeriod = token_refresh_period
        self.baseUrl = self.updateBaseUrl(address , port )

    def set_debug_level(self , level ) :
        self.logger.set_level(level)    

    def updateBaseUrl( self, address, port ) :
            self.baseUrl = f"https://{address}:{port}/wavesuite/se/api"
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
        self.seLogout()
        self.seAuthentication()
        self.logger.info(f'Auto Token refresh completed.')


    def seAuthentication(self,autoRefresh=True) :
        self.logger.info('Starting to authenticate with service enablement platform ..')
        url = f'{self.baseUrl}/v1/authentication/login'
        self.logger.info(f"Authentication Params: username={self.seUsername}  tenantId={self.tenantId} password=********")
        payload = {
            'username' : self.seUsername ,
            'password' : self.sePassword ,
            'tenantId' : self.tenantId
        }
        headers = {'Content-type': 'application/json'}
        self.logger.debug(f'Authentication Payload: {payload}')
        response = requests.post(url , data=json.dumps(payload) , headers=headers , verify=False)
        self.logger.info(f'Authentication response code={response.status_code}')
        self.logger.debug(f'raw response in authentication {response.text}')
        response = response.json()
        self.accessToken = response['data']['accessToken']
        self.refreshToken = response['data']['refreshToken']
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
        return f"Bearer {self.accessToken}"

    def getAuthorizationToken(self) :
        return self.getBearerToken()

    def seLogout(self) :
        self.logger.info('Starting to logout form service enablement platform ..')
        url = f'{self.baseUrl}/v1/authentication/logout'
        self.logger.info(f"Authentication Params: username={self.seUsername} tenantId={self.tenantId}")
        payload = {'refreshToken' : self.refreshToken }
        headers = self.getRequestHeader()
        self.logger.debug(f'Logout out headers {headers}')
        self.logger.debug(f'Logout out payload {payload}')
        response = requests.post(url , data=json.dumps(payload) , headers=headers , verify=False)
        self.logger.debug(f'raw response in logout {response.text}')
        self.logger.info(f'Logout status code={response.status_code}')

    def seUpdateUserGroup(self , user , group ) :
        username = user.get('userName')
        self.logger.info(f'Starting to update {username} with group {group} ...')
        url= f"{self.baseUrl}/v1/tenants/users/{username}/update"
        payload = {
            'email' : user.get('email') ,
            'externallyManaged' : True , 
            'firstName' : user.get('firstName'),
            'lastName' : user.get('lastName') ,
            'roleName' : group 
        }
        self.logger.debug(f'Updating using form {payload}')
        headers = self.getRequestHeader()
        response = requests.post(url , data=json.dumps(payload) , headers=headers , verify=False)
        self.logger.debug(f'raw response {response.text}')
        self.logger.info(f'Update user {username} status code={response.status_code}')

    def seDeleteUser(self , user ) :
        username = user.get('userName')
        self.logger.info(f'Starting to remove {username} ...')
        url= f"{self.baseUrl}/v1/tenants/users/{username}"
        headers = self.getRequestHeader()
        response = requests.delete(url, headers=headers , verify=False)
        self.logger.debug(f'raw response  {response.text}')
        self.logger.info(f'remove user {username} status code={response.status_code}')

    def seLockUser(self , user ) :
        username = user.get('userName')
        self.logger.info(f'Starting to lock {username} ...')
        url= f"{self.baseUrl}/v1/tenants/users/{username}/lock"
        headers = self.getRequestHeader()
        response = requests.post(url, headers=headers , verify=False)
        self.logger.debug(f'raw response  {response.text}')
        self.logger.info(f'lock user {username} status code={response.status_code}')

    def seUnlockUser(self , user ) :
        username = user.get('userName')
        self.logger.info(f'Starting to unlock {username} ...')
        url= f"{self.baseUrl}/v1/tenants/users/{username}/unlock"
        headers = self.getRequestHeader()
        response = requests.post(url, headers=headers , verify=False)
        self.logger.debug(f'raw response {response.text}')
        self.logger.info(f'unlock user {username} status code={response.status_code}')

    def getRequestHeader( self , extra_header={}) :
        headers = {'Content-type': 'application/json' , 'authorization': f"Bearer {self.accessToken}"}
        headers.update(extra_header)
        return headers

    def getLicense(self) :
        self.logger.info(f'Getting license information...')
        url= f"{self.baseUrl}/v1/license"
        headers = self.getRequestHeader()
        response = requests.get(url, headers=headers , verify=False)
        self.logger.debug(f'raw response {response.text}')
        self.logger.info(f'requesting license status code={response.status_code}')
        if response.status_code == 200 :
            return response.json()
        else :
            return {}
        

    def getUsers(self) :
        self.logger.info(f"Get users from SE ...")
        url= f"{self.baseUrl}/v1/tenants/users"
        headers = self.getRequestHeader()
        self.logger.debug(f'Get users headers = {headers}')
        response = requests.get(url , headers=headers , verify=False)
        self.logger.info(f'Get Usr response code={response.status_code}')
        self.logger.debug(f'raw response in authentication {response.text}')
        if response.status_code == 200 :
            self.logger.debug(f'response is 200 , return the json as dict and filter on data ...')
            self.users = response.json().get('data')
            return self.users
        else :
            self.logger.error(f'Error getting users  {response.text}')
            self.logger.debug(f'response is not 200 , return empty array')
            self.users = []
            return []

if __name__ == '__main__':
    pass



