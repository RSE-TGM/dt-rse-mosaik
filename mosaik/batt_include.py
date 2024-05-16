
# DTSDA
# definizioni di variabili e funzioni varie

import io
import yaml
import json
import uuid
from pathlib import Path
import redis
import os
from loguru import logger

from minio import Minio
import glob
import os
from minio.error import  S3Error

MODSIM = 'SIM'    # era 1
MODLEARN = 'LRN'  # era 10
NOFORZ = '0'      # era 0
FORZSIM = MODSIM
FORZLEARN = MODLEARN
STOP = -1

S_IDLE    = 'Idle'
S_RUNNING = 'Running'
S_LOADED  = 'Loaded'
S_ENDED   = 'Endend'

DTHOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DATA_PATH = DTHOME + "/mosaik/configuration/"

CONFIGDT = "configDT.yaml"

EXPERIMENT_CONFIG = "experiment_config.yaml" 

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
        self.tags = self.configDT['redis']['DTSDA']

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
#            logger.info('Redis Connected!')
        except Exception as ex:
            print ('Error:', ex)
            exit('Failed to connect, terminating.')
        
        logger.info("REDIS: CONNECTED: {redis_host} {redis_port}!!", redis_host=self.redis_host, redis_port=self.redis_port ) 
        return self.red
    
    def check(self):
        try:
            response = self.red.client_list()
            return (self)
        except redis.ConnectionError:
            logger.info("REDIS: NON esiste  il servizio: {redis_host} {redis_port}!!", redis_host=self.redis_host, redis_port=self.redis_port ) 
            return (None)

    def aget(self, tag) :
        return(self.red.get(self.tags[tag][0]).decode('utf-8') )
#        return(self.red.get(tag).decode('utf-8') )
   
    def aset(self, tag, val) :
        return(self.red.set(self.tags[tag][0],val))
            
    def esistetag(self,tag):
        return(self.red.exists(tag))
    
    def gettags(self):
        ret = self.configDT['redis']['DTSDA']
        return(ret)
    
    def chiudi(self):
        return(self.red.close())


class MinioClient(object):
    def __init__(self, endpoint="localhost:9000", access_key="4K10mbUN3FxVsDxtDYSh", secret_key="sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD", secure=False ):
        self.config_data_path = CONFIG_DATA_PATH
        self.configDT = CONFIGDT 
        self.configDT = readConfig(self.config_data_path, self.configDT)
        self.endpoint = self.configDT['minio']['ENDPOINT']
        self.access_key=self.configDT['minio']['ACCESS_KEY']
        self.secret_key=self.configDT['minio']['SECRET_KEY']
        self.secure=self.configDT['minio']['SECURE']
        
        self.indexname = self.configDT['minio']['INDEXNAME']
        self.indexcontext = self.configDT['minio']['INDEXCONTEXT']
        self.indexbucket = self.configDT['minio']['INDEXBUCKET']

        self._indexctx = self.configDT['minio']['INDEX_CTX']
        self._indexuid = self.configDT['minio']['INDEX_UID']
        self._indexname = self.configDT['minio']['INDEX_NAME']
        self._indexdescription = self.configDT['minio']['INDEX_DESCRIPTION']
        self._indexdata = self.configDT['minio']['INDEX_DATA']


        # self.endpoint=endpoint
        # self.access_key=access_key
        # self.secret_key=secret_key
        # self.secure=secure
        self.client = Minio( endpoint = self.endpoint,
                            access_key = self.access_key,
                            secret_key = self.secret_key,
                            secure = self.secure )

        logger.info("MINIO: CONNECTED: {minio_host} !!", minio_host=self.endpoint ) 

    def object_exists(self, bucket, obj_path) -> bool:
        try:
            self.client.stat_object(bucket, obj_path)
            return True
        except S3Error as _:
            return False

    def upload_to_minio(self, local_path, bucket_name, minio_path):
    #    assert os.path.isdir(local_path)
        for local_file in glob.glob(local_path + '/**'):
            local_file = local_file.replace(os.sep, "/") # Replace \ with / on Windows
            if not os.path.isfile(local_file):
                minio_path_new = minio_path + "/" + os.path.basename(local_file)
                self.upload_to_minio(local_file, bucket_name, minio_path_new)
            else:
                remote_path = os.path.join(minio_path, os.path.basename(local_file))
                remote_path = remote_path.replace(os.sep, "/")  # Replace \ with / on Windows
                self.client.fput_object(bucket_name, remote_path, local_file)

    def download_from_minio(self, minio_path, bucket_name, dst_local_path):
    # for bucket_name in client.list_buckets():
        for item in self.client.list_objects(bucket_name, prefix=minio_path, recursive=True):
#        for item in self.client.list_objects(bucket_name, start_after=minio_path, recursive=True):
            full_path = os.path.join( dst_local_path,  item.object_name[len(minio_path):])
#            full_path = os.path.join( dst_local_path,  os.path.basename(item.object_name))
            full_path = full_path.replace(os.sep, "/") # Replace \ with / on Windows
            print(item.object_name)
            self.client.fget_object(bucket_name,item.object_name,full_path)
    
    def read_index(self):
        if  self.object_exists(self.indexbucket, self.indexname):
            findex = open(self.indexname)
            data_index = json.load(findex)
            findex.close()
            return ( data_index )
        else:
            return(None)

    def add_to_index(self, newconf, newdescr):
        if  self.object_exists(self.indexbucket, self.indexname):
            # findex = open(self.indexname, "rw")
            # data_index = json.load(findex)
            struid =  str(uuid.uuid4())
            datafield = self.indexbucket + "/" + newconf
            entry={newconf: {
                    self._indexctx:  self.indexcontext,
                    self._indexuid: struid,
                    self._indexname: newconf,
                    self._indexdescription: newdescr,
                    self._indexdata: datafield
                    }}
            with open(self.indexname, "r+") as file:
                data = json.load(file)
                data.append(entry)
                file.seek(0)
                json.dump(data, file)
                file.close()
            return ( data )        
        pass


class InfluxDBCli(object):
    def __init__(self, influx_sim):
        self.config_data_path = CONFIG_DATA_PATH
        self.configDT = CONFIGDT 
        self.configDT = readConfig(self.config_data_path, self.configDT)
        self.url = self.configDT['influxdb']['URL']
        self.org = self.configDT['influxdb']['ORG']
        self.bucket = self.configDT['influxdb']['BUCKET']
        self.token = self.configDT['influxdb']['TOKEN']
        self.measurement = self.configDT['influxdb']['MEASUREMENT']
        
        self.influx = influx_sim.Database(
           url=self.url,
           org=self.org,
           bucket=self.bucket,
           token=self.token,
           measurement=self.measurement )
                  
    def getinflux(self):
        return (self.influx)



# MINIO_ENDPOINT = "localhost:9000"
# MINIO_ACCESS_KEY = "4K10mbUN3FxVsDxtDYSh"
# MINIO_SECRET_KEY = "sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD"
# MINIO_SECURE = False
            
# minio_client = MinioClient(endpoint="localhost:9000", 
#                            access_key="4K10mbUN3FxVsDxtDYSh", 
#                            secret_key="sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD", 
#                            secure=False )

# local_path = "/home/antonio/dtwin/dt-rse-mosaik/mosaik/configuration"
# bucket_name = "sda-dt"
# minio_path = "configuration"

# minio_client.upload_to_minio(local_path, bucket_name, minio_path)


# minio_path = "conf1/"
# dst_local_path = "/home/antonio/temp4"
# minio_client.download_from_minio(minio_path, bucket_name, dst_local_path)
