
# This script is used to collect data from Nokia 1830PSS WDM
# update on 15-12-2022 : 10:53

import sys
import traceback
import paramiko , json , csv ,sys
from time import sleep
from datetime import datetime
from easy_utils_dev.debugger import DEBUGGER

class PSS1830 :
    
    TIMEOUT = 30
    PROMPT_RE = None
    CTRL_C = '\x03'

    def __init__(self , sim=False ) -> None:
        self.port = 22
        self.logger = DEBUGGER('1830PSSCLI')
        self.connected = False
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.channel = None
        self.nodeName = None
        self.prompt = None
        self.TIMEOUT = 1.5
        self.isjumpserver = False
        self.jumpserver = {}
        self.sim = sim
        self.jumpServerInSameInstance  = False
        self.requireAknow=None
        self.pssRelease = None

    def nfmtJumpServer(self, ip , usr , pw  ) :
        self.logger.info(f"""ssh to nfmt vm nsested ssh  [ ip  =>  {ip} ] ..""")
        try :
            self.jumpServerInSameInstance = True
            self.jumpserver  = paramiko.SSHClient()
            self.jumpserver.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.jumpserver.connect(ip  , self.port , usr , pw )
            self.isjumpserver = True
            self.nfmtip = ip 
            self.nfmtsshuser = usr
            self.nfmtsshpw = pw
            self.logger.debug(f"""check if tcpfowarding is allowed or not .. """)
            stdin, stdout, stderr = self.jumpserver.exec_command("cat /etc/ssh/sshd_config | grep -i AllowTcpForwarding")
            result = stdout.readlines()
            self.logger.debug(f"""check if tcpfowarding is allowed or not. Result : {result}""")
            for line in result :
                if "#" in line : continue 
                if 'no' in line :
                    self.logger.debug(f"""check if tcpfowarding is allowed or not. result is disallowed. fixing .. """)
                    self.fixTcpSSH()
                    self.jumpserver.close()
                    self.logger.debug(f"""re-establish the connection [ jumpserver ] after modifying the sshd file and restarting the sshd service ..""")
                    self.jumpserver  = paramiko.SSHClient()
                    self.jumpserver.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.jumpserver.connect(ip  , self.port , usr , pw )

            self.logger.info(f"""ssh to nfmt vm nsested ssh  [ ip  =>  {ip} ] [ CONNECTED ]""")
            self.connected = True
            # to have the nfmtip inside the jumpserver if needed to be injected into connect function later from another created class
            self.jumpserver.nfmtip = ip
            # return the jumpserver in order to have it in case of need to inject it to another paramiko conneciton as sock.
            return self.jumpserver
        except Exception :
            self.logger.debug(f"""ssh to nfmt vm nsested ssh  [ ip  =>  {ip} ] [ FAILED ]  {traceback.format_exc()} """) 
            self.logger.info(f"""ssh to nfmt vm nsested ssh  [ ip  =>  {ip} ] [ FAILED ]""")
            sys.exit(-1)


    def fixTcpSSH(self) :
        return
        self.logger.info(f"""fixing tcp allow tcpforwarding .. """)
        stdin, stdout, stderr = self.jumpserver.exec_command("cat /etc/ssh/sshd_config | grep -i AllowTcpForwarding")
        result = stdout.read()
        self.logger.debug(f"""Current AllowTcpForwarding result = {result}""") 
        cli1 = f"sed -i 's/#AllowTcpForwarding yes/AllowTcpForwarding yes/g' /etc/ssh/sshd_config"
        cli2 = "sed -i 's/#AllowTcpForwarding no/AllowTcpForwarding yes/g' /etc/ssh/sshd_config"
        cli3 = "sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/g' /etc/ssh/sshd_config "
        self.jumpserver.exec_command(f"{cli1} ; {cli2} ; {cli3} ; service sshd restart")
        stdin, stdout, stderr = self.jumpserver.exec_command("cat /etc/ssh/sshd_config | grep -i AllowTcpForwarding")
        result = stdout.read()
        self.logger.debug(f"""Current [ modifications done ]  AllowTcpForwarding result  = {result}""") 

    def rollbackTcp(self) :
        self.logger.info(f"""fixing tcp disable tcpforwarding .. """)
        stdin, stdout, stderr = self.jumpserver.exec_command("cat /etc/ssh/sshd_config | grep -i AllowTcpForwarding")
        result = stdout.read()
        self.logger.debug(f"""Current AllowTcpForwarding result = {result}""") 
        cli1 = f"sed -i 's/AllowTcpForwarding yes/#AllowTcpForwarding no/g' /etc/ssh/sshd_config"
        cli2 = "sed -i 's/#AllowTcpForwarding no/AllowTcpForwarding yes/g' /etc/ssh/sshd_config"
        cli3 = "sed -i 's/AllowTcpForwarding yes/AllowTcpForwarding no/g' /etc/ssh/sshd_config "
        self.jumpserver.exec_command(f"{cli1} ; {cli2} ; {cli3} ; service sshd restart")
        stdin, stdout, stderr = self.jumpserver.exec_command("cat /etc/ssh/sshd_config | grep -i AllowTcpForwarding")
        result = stdout.read()
        self.logger.debug(f"""Current [ modifications done ]  AllowTcpForwarding result  = {result}""") 

    def wrap_cli(self) :
        for i in range(10) :
            sleep(.5)
            new_data = self.channel.recv(2048).decode('utf-8')
            if ("Username") in str(new_data) : 
                self.channel.sendall(self.cliUser + '\n')
                break
        for i in range(10) :
            sleep(.5)
            new_data = self.channel.recv(2048).decode('utf-8')
            if ("password") in str(new_data).lower() : 
                self.channel.sendall(self.cliPw + '\n')
                break
        if self.requireAknow :
            for i in range(10) :
                sleep(1)
                new_data = self.channel.recv(2048).decode('utf-8')
                if ("acknowledge") in str(new_data).lower() : 
                    self.channel.sendall('yes' + '\n')
                    break
        return True

    def determine_prompt(self) :
        for i in range(30) :
            sleep(.5)
            new_data = self.channel.recv(4096).decode('utf-8')
            if "#" in new_data :
                new_data = new_data.split('\n')
                self.prompt = new_data[-1]
                self.logger.debug('prompt detected => '+self.prompt)
                self.nodeName = self.prompt.replace('#' , '')
                self.disable_paging()
                return True


    def ssh_execute(self , ssh ,command ,  merge_output=False , hide_output=False) :
        self.logger.info(f"executing {command}")
        try :
            stdin_ , stdout_ , stderr_ = ssh.exec_command(command)
            r = stdout_.read().decode()
            e = stderr_.read().decode()
            if r.endswith('\n') :
                r = r[ : -1]
            if hide_output : 
                self.logger.debug(f""" 
                =========================
                +command = '{command}'
                -stdout = {r}
                -stderr = {e}
                =========================
                """)
            else :
                self.logger.info(f""" 
                =========================
                +command = '{command}'
                -stdout = {r}
                -stderr = {e}
                =========================
                """)
            if merge_output :
                return str(r) + str(e)
            return r 
        except Exception as error :
            self.logger.info(traceback.format_exc())
            return str(error)
        


    def connect(self , mode='cli' , neip=None , port=22  , user = 'admin', pw ='admin' , rootpw='ALu12#' ,  jumpserver = None ) :
        self.logger.info(f'Opening SSH  connection to NE {neip} mode={mode}')

        self.cliUser = user
        self.mode = mode
        self.cliPw = pw

        if self.sim == True :
            port = 22 
        elif self.sim == False :
            port = 5122


        # another method is to inject the jumpserver inside the connect itself.
        if jumpserver != None  and self.jumpServerInSameInstance == False :
            self.isjumpserver = True
            self.jumpserver = jumpserver
            self.nfmtip = jumpserver.nfmtip 

        if  self.isjumpserver == False :
            self.client.connect(neip , port , "root" , rootpw )

        elif self.isjumpserver :
            jump_transport = self.jumpserver.get_transport()
            src_addr = (self.nfmtip, 22 )
            dest_addr = (neip , port )
            jump_channel = jump_transport.open_channel("direct-tcpip", dest_addr, src_addr)
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(neip , port , "root" , rootpw , sock=jump_channel)
            self.connected = True

        if mode == 'ssh' : 
            self.connected = True
            return self.client

        # getting the ne version.
        self.logger.info(f'Getting NE version.. ')
        cli = "cat /pureNeApp/EC/swVerInfoAscii"
        self.logger.debug(f'Calling {cli}')
        result = self.ssh_execute( self.client , cli )
        if len(result) < 5 :
            raise Exception('PSS Release is not valid')
        elif '-' in result :
            self.pssRelease = float(result.partition('-')[2].partition('-')[0])
            if self.pssRelease < 23.6 :
                self.logger.debug(f'switching to require aknow mode')
                self.requireAknow = True
            else :
                self.logger.debug(f'switching to NOT require aknow mode')
                self.requireAknow = False
        else :
            raise Exception('undefined PSS Release return output. check logs ')         
        
        
        # self.pssRelease

        # if the mode is cli
        self.channel = self.client.invoke_shell()
        self.channel.settimeout(self.TIMEOUT)

        # send the su command
        cmd = 'su - cli\n'
        self.logger.debug(f'Execuing {cmd} to switch from root to cli ..')
        self.channel.sendall(cmd)

        self.wrap_cli()

        self.determine_prompt()

        self.connected = True

        return self.client
        

    def getTime(self) :
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
        return dt_string

        
    def disconnect(self) :
        self.close_cliconnection()
        self.client.close()


    def disable_paging(self) :
        cli = f'paging status disable'
        self.cli_execute(cli , wait=False)
        self.logger.info('paging disabled.')
        

    def channels_report(self, exportCsv=True) :
        self.logger.info('Generating Channels Report .. ')
        channels = self.get_xcs()
        header = ['NE', 'shelf', 'slot', 'port' , 'powerRx' , "powerTx" , "channel" , "prefec"  ,"postFec" , "shape" , "phase" , "trackMode"]
        csvFpath = f"channels_report_{self.host}_{self.getTime()}.csv"
        
        if exportCsv :        
            csvFile = open(csvFpath, 'w', encoding='UTF8' , newline='')
            csvFile = csv.writer(csvFile)
            csvFile.writerow(header)
     
        for channel in channels :
            otPort = None
            
            if not "LINE" in channel['aEnd'].upper() : otPort = channel['aEnd']
            if not "LINE" in channel['zEnd'].upper() : otPort = channel['zEnd']

            file = self.cli_execute(f"show interface {otPort} detail").splitlines()

            for line in file :
                breakIt = False 
                try :
                    nodeName = self.prompt.replace("#" , "")

                    if "Shelf:" in line :
                        details = line.split(": ")
                        shelf = details[1].replace(' Slot' , "")
                        slot = details[2].replace(' Port' , "")
                        port = details[3].split(' -')[0]
                        

                    if "Received Power" in line :
                        powerRx = line.split(':')[1].split(" ")[1]


                    if "Transmitted Power" in line :
                        powerTx = line.split(':')[1].split(" ")[1]

                    if "Channel Tx   " in line :
                        channel = line.split(':')[1].split(" ")[1].replace('\n' , '')

                    if "pre" in line.lower() and 'fec' in line.lower() :
                        prefec = line.split(':')[1].split(" ")[1].replace('\n' , '')

                    if "post" in line.lower() and 'fec' in line.lower() :
                        postFec = line.split(':')[1].split(" ")[1].replace('\n' , '')

                    if "Txshape" in line :
                        shape = line.split(':')[1].split(" ")[1].replace('\n' , '')

                    if "Phase encoding Mode" in line :
                        phase = line.split(':')[1].split(" ")[1].replace('\n' , '')

                    if "TrackPolar" in line or "Track Polar" in line :
                        trackMode = line.split(':')[1].split(" ")[1].replace('\n' , '')
                        breakIt = True

                    if breakIt and  exportCsv :
                        output = f"{nodeName} => [ {shelf} / {slot} / {port}  ] {channel} => TX : {powerTx} ,  RX : {powerRx} prefec => {prefec}  "
                        data = [nodeName , shelf , slot , port , powerRx , powerTx , channel , prefec  ,postFec , shape , phase , trackMode]
                        csvFile.writerow(data)
                        # print(output)

                except Exception as error:
                    print(error) 
                    pass

        self.logger.info('Generating Channels Report Terminated. ')
            
            

    def cli_execute(self , command , wait=True) :
        self.channel.sendall(command + '\n')
        self.logger.info('executing :'+command)
        if wait :
            result = self.wait_result(command)
            return result
        else :
            sleep(.75)
            self.channel.recv(99999999)

    
    def config_database(self , ip , user, password , protocol , path , backupname="BACKUP") :
        self.cli_execute(f'config database server ip {ip}')
        self.cli_execute(f'config database server protocol {protocol}')
        self.cli_execute(f'config database path {path}{backupname}')
        self.cli_execute(f'config database server userid {user}' , wait=False)
        sleep(.5)
        self.cli_execute(password)
  
    def config_swserver(self , ip , user, password , protocol , path ) :
        self.cli_execute(f'config software server ip {ip}')
        self.cli_execute(f'config software server protocol {protocol}')
        self.cli_execute(f'config software server root {path}')
        self.cli_execute(f'config software server userid {user}' , wait=False)
        sleep(.5)
        self.cli_execute(password)
  
    def backToCliRoot(self) :
        self.cli_execute('mm')
        
        
    def wait_result(self , command , expect=None ) :
        
        if not expect :
            expect= self.prompt
        
        self.logger.debug(f"""Wait result syntax : command = {command}""")
        buffer = ''
        while True:
            sleep(.5)
            try :
                new_data = self.channel.recv(4194304).decode('utf-8')
                buffer += new_data
                self.logger.debug(f"""Appending buffer {new_data}""")
            except :
                self.logger.debug(f"""buffer completed""")
                break
        nbuffer = ''
        for index , line in enumerate(buffer.splitlines()) :
            if command in line and self.prompt in line : 
                continue
            nbuffer += line + '\n'

        return nbuffer

    
    def get_allcards(self) : 
        self.logger.info("Getting all cards inventory .. ")
        cards = self.cli_execute('show slot *')
        self.logger.debug(f"Getting all cards inventory .. return {cards} ")
        cards = cards.splitlines()
        cards_return = {"all" : {} , "equipped" : {} , "unequipped" : {} }
        for key , line in enumerate(cards) : 
            if "------------" in line : continue
            
            if 'Slot' in line or 'Present Type' in line  or'see slot' in line or "Oper" in line : continue
            
            _card_line = [x for x in line.split(' ') if x != '' ]
            
            if 'Empty' == _card_line[1] : continue
            
            self.logger.debug(f"get_allcards : line split .. return {_card_line} ")

            slotting = _card_line[0]
            cardType = _card_line[1]
            
            
            
            cards_return['all'][slotting] = {'card' : cardType , 'slot' : slotting , 'status' : _card_line[-1]}
            if "UEQ" in line :
                cards_return['unequipped'][slotting] = {'card' : cardType , 'slot' : slotting ,  'status' : _card_line[-1] }
            else :
                cards_return['equipped'][slotting] = {'card' : cardType , 'slot' : slotting ,  'status' : _card_line[-1] }
        self.logger.debug(f"get_allcards : final return {cards_return}")
        # open('./text.json' , 'w' ).write(json.dumps(cards_return))
        return cards_return  
            




    def get_xcs(self) :
        xcs = self.cli_execute('show xc *')
        xcs = xcs.splitlines()
        xcsList = []
        for key , line in enumerate(xcs) : 
            # print(f">>> {line}")
            # print(line)
            if "------------" in line : continue
            if "A-End" in line or 'OCH Trail' in line or "Admin Oper" in line or "entries" in line or " "*20 in line : continue
            
            details = line.split(' ')
            
            details = [ i for i in details if i != "" ]
            if len(details) == 0 : 
                continue
            
            try :
                aEnd = details[0]
                zEnd = details[1]
                channel = details[2]
                connectionId = details[3]
                label = details[4]
                width = details[5]
                type = details[6]
                adminState = details[7]
                oper = details[8]
                dir = details[9]
            except :
                continue
                
            tmp = {'aEnd' : aEnd , 'zEnd' : zEnd , 'channel' : channel , "id" : connectionId ,
                   "label" : label , 'width' : width , "type" : type , "admin" : adminState , 
                   "operation" : oper , 'dir' : dir
                   }
            xcsList.append(tmp)
        
        open('./xsList.json' , 'w').write(json.dumps(xcsList))
        return xcsList        
         
    def get_cards(self) :
        cards = self.cli_execute('show card inven *')
        raw_return = cards
        cards = cards.splitlines()
        cardsJson  = []
        for line in cards :
            if line == '' or "Location  Card" in line or "--"*10 in line : continue 
            card = line.split(' ')
            cardsList = [ i for i in card if i != "" ]
            shelfSlot = cardsList[0]
            shelf = shelfSlot.split('/')[0]
            slot = shelfSlot.split('/')[1]
            family = cardsList[1]
            cardType = cardsList[2]
            pn = cardsList[3]
            sn = cardsList[4]
            cardsJson.append({
                "shelfSlot" : shelfSlot , 'shelf' : shelf , 'slot' : slot ,'family' : family , "cardType" : cardType , "pn" : pn  , 'sn'  : sn
            })
            
        # print(cardsJson)
        return cardsJson , raw_return

    def get_userlabel(self) :
        result = self.cli_execute('show general userlabel')
        return result

    
    def enable_openagent(self) :
        self.cli_execute('config general openagent enabled')

    def disable_openagent(self) :
        self.cli_execute('config general openagent disable')

    def openagent_status(self) :
        result = self.cli_execute('show general openagent').splitlines()
        for line in result :
            if ":" in line :
                status = line.split(':')[1]
                if "enabled" in status.lower() :
                    status  = True
                elif 'disabled' in status.lower() :
                    status =  False
                else :
                    status =  'Unknown'
        
        self.logger.info(f'Open Agent Status = {status}')
        return status
        
    def get_odukxc(self) : 
        odukxs = self.cli_execute('show odukxc brief')
        odukxs = odukxs.splitlines()
        odukxsList = []
        for key , line in enumerate(odukxs) : 
            if "------------" in line : continue
            if "A-End" in line or 'XcRate' in line or "Admin Oper" in line or "entries" in line or " "*20 in line : continue
            details = line.split(' ')
            details = [ i for i in details if i != "" ]
            if len(details) == 0 : continue
            aEnd = details[0]
            zEnd = details[1]
            id = details[2]
            rate = details[3]
            dir = details[4]
            prot = details[5]
            name = details[6]
            odukxsList.append({
                'aEnd' : aEnd , "zEnd" : zEnd  , "id" : id , "rate" : rate , "dir" : dir , "protection" : prot , 
                "name" : name
            })
            
        # print(odukxsList)
        return odukxsList
        
    def get_version(self) :
        # results = self.cli_execute('show version').splitlines()
        # versionIs = ''
        # for line in results :
        #     if "Version" in line :
        #         versionIs = line.split(':')[1].replace(' ' , "")
        #         return versionIs
        return self.pssRelease
        
    def close_cliconnection(self) :
        self.cli_execute('mm' , False)
        self.cli_execute('logout' , False)
        self.connected = False
    
    def get_mastershelf(self) :
        masterShelf = self.get_shelfs()[0]['type']    
        self.logger.info(f'Master Shelf Type : {masterShelf}')
        return masterShelf

    def get_nefirmware(self) :
        self.logger.info('Getting NE firmware .. ')        
        cli = f"show firmware ne"
        result = self.cli_execute(cli)
        data = []
        result = result.splitlines()
        for line in result :
            if 'sh/sl' in line or '----------' in line or line == ''  or "NE" in line : continue
            s = line.split(' ')
            s = [ x for x in s if x != '' ]
            # print(s)
            shelfslot = s[0]
            shelf = shelfslot.split('/')[0]
            slot = shelfslot.split('/')[1]
            card = s[1]
            try : 
                profile= s[2]
            except IndexError :
                profile= 'N/A'
                
            data.append({'shelf' : shelf , 'slot' : slot ,  'shelf/slot' : shelfslot , 'card' : card , 'profile' : profile  })
        
        # print(data)
        self.logger.info('Getting NE firmware .. completed') 
        return data

    def get_availableFW(self) :
        self.logger.info('Getting available firmware .. ')        
        cli = f"show firmware available"
        result = self.cli_execute(cli)
        self.logger.info(f'get_availableFW : command = {cli}')    
        self.logger.debug(f'{self.nodeName} - {cli} - {result}')
        result = result.splitlines()
        data = {}
        start = False
        current_fw = 'Not Found'
        for line in result :
            if 'All available firmware profiles' in line :
                card = line.split('for')[1].replace(' ', '').replace('\n' , '')
                start = True
                profiles = []
                shouldEnd = True    
            elif start == True :
                if line != '' :
                    fw = line.replace(' ', '').replace('\n' , '').replace('*' , '')
                    profiles.append(fw)
                    data[card] = {'profiles' : profiles , 'currentfw' :  current_fw}
                if "*" in line : 
                    current_fw = line.replace(' ', '').replace('\n' , '').replace('*' , '')
                    data[card] = {'profiles' : profiles , 'currentfw' :  current_fw}


        # open('./d.json' , 'w').write(json.dumps(data))  
        self.logger.info('Getting available firmware .. completed') 
        self.logger.debug(f'Getting available firmware {data}') 
        return data

    def get_shelfs(self) :
        self.logger.info('Getting shelfs .. ')
        shelfsList = []
        cli = f"show shelf *"
        shelfs = self.cli_execute(cli).splitlines()
        for line in shelfs :
            if ("Shelf" and "Connectivity" in line )  or "--"*20 in line : continue
            details = [i for i in line.split(' ') if i != '']
            
            if len(details) == 0 : continue 

            shelfsList.append({
                'shelfId' : details[0],
                'type' : details[1]
            })
        
        self.logger.info('Getting shelfs Terminated ')
        return shelfsList


if __name__ == '__main__' : 
    pass

        
# pss = PSS1830()
# jumpserver = pss.nfmtJumpServer('135.183.142.200' , 'root' , 'install10')
# pss = PSS1830()
# x= pss.connect('ssh' , neip="10.10.20.1" , jumpserver=jumpserver )
# x = pss.get_allcards()
# print(x)
# s = pss.get_nefirmware()
# print(s)
# pss.get_mastershelf()
# pss.disable_openagent()
# pss.enable_openagent()
# pss.openagent_status()
# pss.get_version()
# pss.get_xcs()
# pss.channels_report()

# pss.cli_execute('show xc *')
# s = pss.close_cliconnection()
# s = pss.cli_execute('show otu *')
# print(s)
# pss.cli_execute('show shelf *' , False)
# pss.cli_execute('show version')
# pss.cli_execute('show soft up st')
# pss.cli_execute('show card inven * ')
# pss.config_database('10.10.10.1' , 'alcatel' , 'alu1233' , 'ftp' , '/' , 'BACKUP')
# pss.config_swserver('10.10.10.2' , 'alcatel' , 'alu1233' , 'ftp' , '/')
