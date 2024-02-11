
# DTSDA
# definizioni di variabili e funzioni varie

import yaml
from pathlib import Path
import redis
import os
from loguru import logger

MODSIM = 'SIM'    # era 1
MODLEARN = 'LRN'  # era 10
NOFORZ = '0'      # era 0
FORZSIM = MODSIM
FORZLEARN = MODLEARN
STOP = -1

CONFIG_DATA_PATH = "mosaik/configuration/"
CONFIGDT = "configDT.yaml"  

def readConfig(config_path, namefile):
        # Read in memory a yalm file
        
        #config_path = "mosaik/configuration/"
        #namefile = "experiment_config.yaml"
        try:
            with open(Path(config_path) / Path(namefile), 'r') as fin:
                ret = yaml.safe_load(fin)
                fin.close()
                return ret
        except Exception:
            raise FileExistsError("Selected configuration file doesn't exist.")
            return None 

class  redisDT(object):
    def __init__(self):
        self.config_data_path = CONFIG_DATA_PATH
        self.configDT = CONFIGDT 
        self.configDT = readConfig(self.config_data_path, self.configDT)

        self.redis_host = os.getenv(self.configDT['redis']['redis_host'])
        if self.redis_host == None:
            self.redis_host = self.configDT['redis']['redis_host_default']

        self.redis_port = os.getenv(self.configDT['redis']['redis_port'])
        if self.redis_port == None:
            self.redis_port = self.configDT['redis']['redis_port_default']

    #self.redis = redis.Redis(host=redis_host, port=redis_port, ch
    def connect(self):
        try:
            self.red  = redis.Redis(host=self.redis_host,port=self.redis_port)   
            print (self.red)
            self.red.ping()
            logger.info('Redis Connected!')
        except Exception as ex:
            print ('Error:', ex)
            exit('Failed to connect, terminating.')
        
        logger.info("REDIS: CONNESSO: {redis_host} {redis_port}!!", redis_host=self.redis_host, redis_port=self.redis_port ) 
        return self.red
    
    def check(self):
        try:
            response = self.red.client_list()
            return (self)
        except redis.ConnectionError:
            logger.info("REDIS: NON esiste  il servizio: {redis_host} {redis_port}!!", redis_host=self.redis_host, redis_port=self.redis_port ) 
            return (None)

    def aget(self, tag) :
        return(self.red.get(tag).decode('utf-8') )
   

    def aset(self, tag, val) :
        return(self.red.set(tag,val))
            
    def esistetag(self,tag):
        return(self.red.exists(tag))
    
    def gettags(self):
        ret = self.configDT['redis']['DTSDA']
        return(ret)
    
    def chiudi(self):
        return(self.red.close())

