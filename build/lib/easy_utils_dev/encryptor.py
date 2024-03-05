from cryptography.fernet import Fernet
import base64
from hashlib import sha256

class initCryptor :

    def __init__(self , logger=None , enable_log=True, use_default_logger=True) :
        self.secretKey = 'MEOpticsNpI'
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        self.logger = logger
        self.enable_log = enable_log

        if use_default_logger :
            self.setup_logger()

    def setup_logger( self ) :
        from .debugger import DEBUGGER
        self.logger = DEBUGGER('easy-Cryptor')
        

    def log( self , message ) :
        if self.logger and self.enable_log :
            self.logger.info( message )

    def en_Fehrnet(self,message) :
        self.log(f'using Fehrnet to encrypt {message}')
        encMessage = self.fernet.encrypt(message.encode())
        return encMessage.decode('utf-8')

    def dec_Fehrnet(self, message) :
        self.log(f'using Fehrnet to decencrypt {message}')

        try :
            self.log(f'encoding message...')
            message = message.encode()
            self.log(f'message after encoding {message}')
        except  : 
            self.log(f'skipping encoding message! ignore')
            pass 
        decMessage = self.fernet.decrypt(message).decode()
        return str(decMessage)


    def en_base64(self,message) :
        self.log(f'encoding base64 message {message}')
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        self.log(f'encoding base64 message base64={base64_message}')
        return base64_message
    
    def dec_base64(self,message) :
        self.log(f'decoding base64 message base64={message}')
        base64_bytes = message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        self.log(f'decoding base64 message utf-8={message}')
        return message 


if __name__ == '__main__' :
    pass

