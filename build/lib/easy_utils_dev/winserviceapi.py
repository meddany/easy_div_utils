from .uiserver import UISERVER
from .debugger import DEBUGGER
import subprocess
from .utils import generateToken , getTimestamp
from flask import request
from traceback import format_exc
import os
import json
import psutil
from threading import Thread
from time import sleep
class WinServiceApi() :
    def __init__(self, debugger_path, port=7718,username='admin' , password='Nokia@2023' , require_auth=True) -> None:
        self.logger = DEBUGGER('WinServiceApi' , homePath=debugger_path)
        self.ui = UISERVER(address='127.0.0.1', port=port,https=True)
        self.services = {}
        self.logger.set_level('debug')
        self.token = 'not-allowed-ever-forever'
        self.username = username
        self.password = password
        self.require_auth = require_auth
        self.started = getTimestamp()
        self.url_validation_exceptions = [
            '/service/api/winservice/login' ,
            '/service/api/winservice/check' ,
        ]
        pass 

    def run(self) :
        self.ui.startUi(True)
        self.app = self.ui.getFlask()
        self.wrapper()
        self.socket = self.ui.getSocketio()

    def buildReturnCode(self , process) :
        if process.returncode == 1 or process.returncode == None :
            rc = 1
        elif process.returncode == 0 :
            rc = 0
        else:
            rc = 1
        return rc

    def check_pid_running(self , pid):
        if pid == 0 :
            return False
        return psutil.pid_exists(pid)

    def get_child_pids(self , parent_pid):
        self.logger.debug(f'looking for child {parent_pid}')
        cli = f'''wmic process get Caption,ParentProcessId,ProcessId | findstr "{parent_pid}"'''
        a = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
        a=a.stdout.readlines()
        for line in a :
            if line.startswith('\n'): continue
            line= line.split(' ')
            line = [x for x in line if x != '' ]
            if str(line[1]) == str(parent_pid) :
                self.logger.debug(f'looking for child {parent_pid} completed.')
                return int(line[2])
        return 0
    
    def getPidByServiceName(self , serviceName):
        cli = f'''wmic process get Caption,ParentProcessId,ProcessId | findstr "{serviceName}"'''
        a = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
        a=a.stdout.readlines()
        for line in a :
            if line.startswith('\n'): continue
            line= line.split(' ')
            line = [x for x in line if x != '' ]
            if str(serviceName)  in str(line[0]):
                return int(line[2])
        return 0


    def get_process_details(self, pid):
        try:
            # Get process information by PID
            process = psutil.Process(pid)
            # Get process details
            details = {
                'pid': process.pid,
                'name': process.name(),
                'cmdline': process.cmdline(),
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info(),
                'create_time': process.create_time(),
                'status': process.status(),
                'username': process.username(),
                'connections': process.connections(),
                # Add more details as needed
            }
            return details
        except psutil.NoSuchProcess:
            return {}

    def requireValidation(self , url ) :
        if not self.require_auth :
            return False
        for elem in self.url_validation_exceptions :
            if elem in url :
                return False
        return True

    def wrapper(self) :
        
        @self.app.before_request
        def validate() :
            if self.requireValidation(request.url) :
                self.logger.debug(request.headers)
                if request.headers.get('Authorization' , 'not-allowed') != self.token :
                    return json.dumps({"status" : 400 , 'message' : 'Invalid Authorization.'})


        @self.app.route('/service/api/winservice/login' , methods=['POST'])
        def get_token() :
            try :
                if not self.require_auth :
                    raise Exception("Required authentication is disabled. you can call api without authentication.")
                if request.form.get('username') != self.username or  request.form.get('password') != self.password :
                    raise Exception('Invalid username or password')
                self.token = generateToken(30)
                return json.dumps({"status" : 200 , 'token' : self.token })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/check' , methods=['GET'])
        def check_Connection() :
            try :
                now = getTimestamp()
                uptime = now - self.started
                return json.dumps({"status" : 200 , 'uptime' : uptime , 'unit' : 'seconds' , 'startTimestamp' : self.started , 'nowTimestamp' : now })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
            
        @self.app.route('/service/api/winservice/run' , methods=['POST'])
        def api_win_run_service() :
            try :
                self.logger.debug(request.form)
                serviceName = request.form.get('serviceName')
                serviecPath = request.form.get('servicePath')
                stream = request.form.get('stream' , 'true' )
                autoRestart = request.form.get('autoRestart' , 'true' )
                tries = int(request.form.get('tries' , 3 ))
                command = request.form.get('command' , 'false' )
                verifyService = request.form.get('verifyService' , 'true' )
                if verifyService == 'true' :
                    pid = self.getPidByServiceName(serviceName)
                    self.logger.info(f"verify service pid result is {pid}. 0: service doesnt exists.")
                    if pid != 0 :
                        s,o = subprocess.getstatusoutput(f"taskkill /PID {pid} /F")
                        self.logger.debug(f'killing old service to start new one {pid} | {s} | {o}')
                        for key , value in self.services.items() :
                            if pid == value.get('pid') :
                                id = key
                                try :
                                    self.services[id]['terminate'] = True
                                    process=  self.services[id]['process']
                                    process.terminate()
                                except :
                                    pass
                id = generateToken(4)
                if command == 'false' :
                    if not os.path.exists(serviecPath) :
                        raise Exception(f'service path does not exist.')
                process = subprocess.Popen(serviecPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
                pid = self.get_child_pids(process.pid)
                self.logger.info(f"Service {serviceName} is running with main_pid=[{process.pid}] pid=[{pid}]")
                def stream_api() :
                    self.logger.info(f'stream started for {id}')
                    data = self.services[id]
                    data['stream_started'] = True
                    process = data.get('process')
                    for line in process.stdout:
                        d= json.dumps({'line' : line.strip()})
                        self.logger.debug(d)
                        data['buffer'] += line.strip() + '\n'
                        if stream == 'true' : 
                            self.socket.emit( f"{id}" , d )
                    process.terminate()
                    self.logger.info(f'stream process with {data.get("pid")} terminated.')
                def auto_restart(id) :
                    while True :
                        sleep(2)
                        if self.services[id].get('terminate' , False ) :
                            self.logger.info(f'breaking [{id}] process auto restart, as terminate flag is on.')
                            break
                        process = self.services[id]['process']
                        pid = self.get_child_pids(process.pid)
                        status = self.check_pid_running(pid)
                        self.logger.debug(f'service status for {pid} is running={status}')
                        if self.services[id]['restart_try'] == tries :
                            self.logger.debug(f'service status for {pid} is {status}. maximum restart reached.')
                            break
                        elif not status :
                            self.services[id]['restart_try'] += 1
                            _try = self.services[id]['restart_try']
                            self.logger.info(f'service {id} is down. restarting try={_try}')
                            process.kill()
                            process = subprocess.Popen(serviecPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
                            self.services[id]['process'] = process
                            self.services[id]['pid'] = pid = self.get_child_pids(process.pid)
                            t = Thread(target=stream_api , args=[])
                            t.start()
                    self.logger.info(f'breaking [{id}] process auto restart, terminated.')


                self.services[id] = {'process' : process , 'serviceName' : serviceName , 'stream_started' : False , 'pid' : pid , 'restart_try' : 0, 'buffer' : '' , 'errors': ''  }
                t = Thread(target=stream_api , args=[])
                t.start()
                if autoRestart == 'true' :
                    t = Thread(target=auto_restart , args=[id])
                    t.start()
                return json.dumps({'status' : 200 , 'id' : id })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})

        @self.app.route('/service/api/winservice/status' , methods=['get'])
        def api_win_get_service_status() :
            try :
                try :
                    id = request.args.get('id')
                    data = self.services[id]
                    process = data.get('process')
                    pid = process.pid
                    childs = self.get_child_pids(pid)
                    result = self.check_pid_running(childs)
                    rc = self.buildReturnCode(process)
                except KeyError:
                    result = False
                return json.dumps({'status' : 200 , 'running' : result , 'returncode' : rc })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})

        @self.app.route('/service/api/winservice/stdout' , methods=['get'])
        def api_win_get_service_std() :
            try :
                try :
                    id = request.args.get('id')
                    data = self.services[id]
                    process = data.get('process')
                    rc = self.buildReturnCode(process)
                except KeyError :
                    raise Exception(f'Process with id {id} does not exist.')
                return json.dumps({'status' : 200 , 'stdout' : data.get('buffer' , '').split('\n')  , 'returncode' : rc })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})

        @self.app.route('/service/api/winservice/stop' , methods=['POST'])
        def api_win_get_service_stop() :
            try :
                try :
                    id = request.args.get('id')
                    data = self.services[id]
                    data['terminate'] = True
                    serviceName = data.get('serviceName')
                    process = data.get('process')
                    pid = self.get_child_pids(process.pid)
                except KeyError :
                    raise Exception(f'Process with id {id} does not exist.')
                self.logger.info(f'received request to kill a process with id {id} serviceName={serviceName} pid={pid}')
                if pid == 0 :
                    raise Exception(f'Process with pid {id} does not exist')
                process.terminate()
                cli = f"taskkill /IM '{serviceName}' /F"
                self.logger.info(f'executing stop service using {cli}')
                s,o = subprocess.getstatusoutput(cli)
                return json.dumps({'status' : 200 , 'returncode' : s , 'returntext' : o})
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/get/variable' , methods=['GET'])
        def get_variable() :
            try :
                target = request.args.get('key')
                self.logger.info(f'got request to return value of variable {target}')
                resp = getattr(self, target, 'variable-not-found')
                return json.dumps({'status' : 200 , 'response' : resp })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})

        @self.app.route('/service/api/winservice/logging/change' , methods=['POST'])
        def api_win_get_service_log_change() :
            try :
                level = request.form.get('level')
                self.logger.set_level(level)
                return json.dumps({'status' : 200 , 'message' : f'logger trace level changed to {level}' })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/logging/change/location' , methods=['POST'])
        def api_win_get_service_log_change_loc() :
            try :
                abpath = request.form.get('location')
                self.logger.changeHomePath(abpath)
                return json.dumps({'status' : 200 , 'message' : f'logger trace path changed to {self.logger.homePath}' })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/getdetails' , methods=['GET'])
        def api_win_get_service_log_change_get() :
            try :
                try :
                    id = request.args.get('id')
                    data = self.services[id]
                    process = data.get('process')
                    pid = self.get_child_pids(process.pid)
                except KeyError :
                    raise Exception(f'Process with id {id} does not exist.')
                return json.dumps({'status' : 200 , 'result' : self.get_process_details(pid) })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/getdetails/servicename' , methods=['GET'])
        def api_win_get_service_log_change_get_name() :
            try :
                try :
                    serviceName = request.args.get('serviceName')
                    pid = self.getPidByServiceName(serviceName)
                    result = pid
                    if result != 0 :
                        details = self.get_process_details(pid)
                    else :
                        details = {}
                except KeyError :
                    raise Exception(f'Process with id {id} does not exist.')
                return json.dumps({'status' : 200 , 'pid_exist' : result != 0 , 'pid' : result , 'details' : details  })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/id' , methods=['GET'])
        def api_win_get_service_lid() :
            try :
                serviceName = request.args.get('serviceName')
                pid = self.getPidByServiceName(serviceName)
                result = pid
                id = 0
                if result != 0 :
                    for key , value in self.services.items() :
                        if result == value.get('pid') :
                            id = key
                return json.dumps({'status' : 200 , 'id' :  id })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
            
        @self.app.route('/service/api/winservice/exec' , methods=['POST'])
        def api_execee() :
            try :
                cli = request.form.get('cli')
                s, r = subprocess.getstatusoutput(cli)
                return json.dumps({'status' : 200 , 'result' : r , 'returncode' : s })
            except Exception as error :
                self.logger.error(error)
                self.logger.debug(format_exc())
                return json.dumps({'status' : 400 , 'message' : str(error)})
