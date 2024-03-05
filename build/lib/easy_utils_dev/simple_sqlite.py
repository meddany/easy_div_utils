from datetime import datetime
import json , sqlite3 , os,subprocess
from .debugger import DEBUGGER
from .utils import getRandomKey
from .custom_env import custom_env , setupEnvironment , insertKey

env = custom_env()

def getLoggerFromMemory( id ) :
    '''
    When Logger/Debugger is called or initialized it automatically is stored in memory with certain id.
    you can call this event from memory by passing that id to this function which will return the event if found.
    if not.. it will return None
    '''
    ev = env.get('simple_sqlite' , {} )
    return ev.get( id , None )


class initDB :
    def __init__(self, logger=None,db=None,useDefaultLogger=False,enable_log=True,id=getRandomKey(n=5)) :

        self.db_file = db
        self.disableLog = False
        self.logger = logger
        self.enable_log = enable_log
        self.id = id
        setupEnvironment( 'simple_sqlite' )
        env['simple_sqlite'][id] = self
        if useDefaultLogger : 
            self.logger = DEBUGGER('DB-CONNECTOR')


    def enable_log( self ) :
        self.enable_log = True
    
    def disable_log( self ) :
        self.enable_log = False

    def database_logger(self, log ) :
        if self.logger and self.enable_log :
            self.logger.info(log)


    def wrapLogger( self , loggerObject ) :
        self.logger = loggerObject
        self.enable_log = True


    def config_database_path(self,path) :
        self.database_logger(f'Database path set to {path}')
        self.db_file = path

        
    def fixTupleForSql(self , list ):
        if len(list) <= 1 :
            execlude = str(list).replace('[' , '(' ).replace(']' , ')')
        else :
            execlude = tuple(list)
        return execlude


    def db_connect(self, timeout=5):
        # self.database_logger(f'DATABASE : Connecting to {self.db_file}')
        try :
            self.con = sqlite3.connect(self.db_file , check_same_thread=False , timeout = timeout)
            self.cur = self.con.cursor()
        except sqlite3.OperationalError:
            self.database_logger('Error : Database Is Locked.')
            self.con = sqlite3.connect(self.db_file , check_same_thread=False , timeout = timeout)
            self.cur = self.con.cursor()
        return self.cur , self.con


    def db_encode(self,db):
        dbf = json.dumps(db)
        return dbf

    def db_decode(self,db) :
        return json.loads(db)



    def execute_dict(self,cli) :
        self.database_logger(f"execute_dict: {cli}")

        cur , conn = self.db_connect()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        c = conn.cursor()
        h = c.execute(cli).fetchall()
        if not 'select' in cli.lower() :
            conn.commit()
        conn.close()
        return h

    def execute(self,cli) :
        self.database_logger(f'Executing : {cli}')

        cur,con = self.db_connect()
        h = cur.execute(cli).fetchall()
        if not 'select' in cli.lower() :
            con.commit()
        con.close()
        return h


    def checkExists(self , cli ) :
        cur , conn = self.db_connect()
        h = cur.execute(cli).fetchall()[0][0]
        if h == 0 :
            conn.close()
            return False
        else : 
            conn.close()
            return True


    def createTable(self,conn, create_table_sql,tableName):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            self.database_logger(f'Creating Table: {tableName}')
            c = conn.cursor()
            h = c.execute(create_table_sql)
            return h
        except Exception as error:
            self.database_logger(f'Creating Table Error: {error}')


    def insert_to_table(self,table_name , table_headers , table_values , autocommit= True , returncli=False) :
        cur , con = self.db_connect()
        self.database_logger(f'Inserting data into {table_name}'.format(table_name=table_name))
        table_headers = tuple(table_headers)
        table_values = tuple(table_values)

        cli = f"INSERT INTO {table_name} {table_headers} VALUES{table_values}"

        if returncli : 
            return cli

        self.database_logger('INFO DB EXECUTION: '+cli)
        cur.execute(cli)
        if autocommit == True :
            con.commit()

        con.close()
        return cur.lastrowid
            
if __name__ == '__main__' :
    pass