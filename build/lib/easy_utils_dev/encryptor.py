from cryptography.fernet import Fernet
import base64
from hashlib import sha256
from .utils import getRandomKey

class initCryptor :

    def __init__(self,random_secretkey=False) :
        if random_secretkey : 
            self.secretKey = getRandomKey(n=15)
        else :
            self.secretKey = 'MEOpticsNpI'
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def en_Fehrnet(self,message) :
        encMessage = self.fernet.encrypt(message.encode())
        return encMessage.decode('utf-8')

    def dec_Fehrnet(self, message) :
        try :
            message = message.encode()
        except  : 
            pass 
        decMessage = self.fernet.decrypt(message).decode()
        return str(decMessage)


    def en_base64(self,message) :
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return base64_message
    
    def dec_base64(self,message) :
        base64_bytes = message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        return message 


if __name__ == '__main__' :
    pass

