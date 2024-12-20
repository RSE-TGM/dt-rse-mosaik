""" Definizioni di variabili globali e definizione di classi e funzioni per DTSDA """

#import io
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

from  DT_rdf import *

def readConfig(config_path, namefile):
        """ Legge file yaml """
        global TZONE
 # Read in memory a yalm file
        
        #config_path = "mosaik/configuration/"
        #namefile = "experiment_config.yaml"
        try:
            with open(Path(config_path) / Path(namefile), 'r') as fin:
                ret = yaml.safe_load(fin)
                logger.info("readConfig: Opening the conf file: {config_path}{namefile}", config_path=config_path, namefile=namefile )

                if "versione" in ret:
                    print(ret['versione'])
                     
                if "tzone" in ret:
                    TZONE=ret['tzone']
                else:
                    TZONE="Europe/Rome"
                
                fin.close()
                return ret
        except Exception:
            raise FileExistsError("Selected configuration (data) file doesn't exist.")
            return None 


class  redisDT(object):
    """ API per connettersi a ad un server redis e utilizzarne le funzionalità """
    def __init__(self):
        self.config_data_path = CONFIG_DATA_PATH
#        self.configDT = CONFIGDT 
#        self.configDT = readConfig(self.config_data_path, self.configDT)
        self.configDT = CURR_CONFIG
#        self.tags = self.configDT['redis']['DTSDA']

        self.redis_host = os.getenv(self.configDT['redis']['redis_host'])
        if self.redis_host == None:
            self.redis_host = self.configDT['redis']['redis_host_default']

        self.redis_port = os.getenv(self.configDT['redis']['redis_port'])
        if self.redis_port == None:
            self.redis_port = self.configDT['redis']['redis_port_default']

    #self.redis = redis.Redis(host=redis_host, port=redis_port, ch
    def connect(self):
        """ Connessione a redis """
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
        """ Check per esistenza della connessione al redis server"""
        try:
            response = self.red.client_list()
            return (self)
        except redis.ConnectionError:
            logger.info("REDIS: NON esiste  il servizio: {redis_host} {redis_port}!!", redis_host=self.redis_host, redis_port=self.redis_port ) 
            return (None)

    def aget(self, simbtag, id='batt1', hmode = False) :
        """ interfaccia semplificata a redis get sia di tag semplici sia di hash"""
        htag= self.configDT['redis']['htags'][0]
        field= self.configDT['redis'][id][simbtag]['field']
        if (not hmode):
            tagg=htag+':'+field
            print(f'get {tagg}')                       
            return(self.red.get(tagg).decode('utf-8') )
#            return(self.red.get(self.tags[simbtag][0]).decode('utf-8') )
        else:  # hash mode
            #ret=self.red.hget(htag, field).decode('utf-8')
#debug            print(f'hget {htag}  {field}')
            return(self.red.hget(htag, field).decode('utf-8'))

    
#        return(self.red.get(tag).decode('utf-8') )
   
    def aset(self, simbtag, val, id='batt1', hmode = False) :
        """ interfaccia semplificata a redis set sia di tag semplici sia di hash"""
        htag = self.configDT['redis']['htags'][0]           # è il tag del hash redis
        field = self.configDT['redis'][id][simbtag]['field']   # id è il tag della batteria, ad esempio 'batt1', simbtag è ad esempio 'DTmode'
        if (not hmode):
            tagg=htag+':'+field
            print(f'set {tagg}')             
            return(self.red.set(tagg,val))
#           return(self.red.set(self.tags[simbtag][0],val))
        else:  # hash mode
            #ret=self.red.hset(htag, field, val)
#debug            print(f'------------------------------>  hset {htag}  {field} {val}')
            return(self.red.hset(htag, field,val))

    
    def hhset(self, simbtag, val, id):
        """ interfaccia semplificata a redis set di variabili hash"""
        htag = self.configDT['redis']['htags'][0]           # è il tag del hash redis
        field = self.configDT['redis'][id][simbtag]['field']   # id è il tag della batteria, ad esempio 'batt1', simbtag è ad esempio 'DTmode'
        #ret=self.red.hset(htag, field, val)
#debug        print(f'hget {htag}  {field} {val}')
        return

    def hhget(self, simbtag, id):
        """ interfaccia semplificata a redis get di variabili hash"""
        htag= self.configDT['redis']['htags'][0]
        field= self.configDT['redis'][id][simbtag]['field']               
        #ret=self.red.hget(htag, field).decode('utf-8')
#debug        print(f'hget {htag}  {field}')
        return
                 
    def esistetag(self,simbtag, id='batt1', hmode = False):
        """ interfaccia semplificata a redis di esistenza sia di tag semplici sia di variabili hash"""
        htag= self.configDT['redis']['htags'][0]
        field= self.configDT['redis'][id][simbtag]['field']  
        if (not hmode):
            tagg=htag+':'+field
            return(self.red.exists(tagg) )
#            return(self.red.exists(self.tags[simbtag][0]) )
        else:
#            retval=self.red.get(self.red.hget(htag, field).decode('utf-8') ) 
            retval=self.red.hget(htag, field) 
            if retval == None : 
                ret=0
            else: ret=1           
        return(ret)
#        return(self.red.exists(tag))
    
    def gettags(self, id='batt1'):
        """ ritorna la tag di base della batteria del DTwin DTSDA"""
#        ret = self.configDT['redis']['DTSDA']
        ret = self.configDT['redis'][id]
        return(ret)
    
    def chiudi(self):
        """ Chiude la connessione al server redis """
        return(self.red.close())

    def readstream(self, stream_name, ind) -> dict :
        """Legge stream redis 

        Args:
            stream_name (str): Nome dello stream
            ind (int): i-esimo elemento dello stream ( per uno stream di 100 elementi ind del più recente è 99)

        Returns:
            dict: Contenuto dello stream ad esempio:  {"Time":"21-10-2024 11:33:39.814245",
            "Tdiff [s]":"1,003","VCEL1 Tensione Cella 1 [V]":"4,167","VCEL2 Tensione Cella 2 [V]":"4,166",
            "VCEL3 Tensione Cella 3 [V]":"4,161","VCEL4 Tensione Cella 4 [V]":"4,161","CEL5 Tensione Cella 5 [V]":"4,153",
            "VCEL6 Tensione Cella 6 [V]":"4,153","VCEL7 Tensione Cella 7 [V]":"4,162","VCEL8 Tensione Cella 8 [V]":"4,162","VCEL9 Tensione Cella 9 [V]":"4,154",
            "VCEL10 Tensione Cella 10 [V]":"4,155","VCEL11 Tensione Cella 11 [V]":"4,155","VCEL12 Tensione Cella 12 [V]":"4,158","VCEL13 Tensione Cella 13 [V]":"4,158","VCEL14 Tensione Cella 14 [V]":"4,160",
            "VMOD1 Tensione Modulo 1 [V]":"29,073","CURR1 Corrente Modulo 1 [A]":"-20,695","TMOD1 Temperatura Modulo 1 [�C]":"21,486","TAMB Temperatura Ambiente 1 [�C]":"21,673",
            "TimestampFile":"2024-02-19 15:30:11"}
        """        
        """  interfaccia semplificata a redis di lettura di variabili stream """
                   #messages = r.xread({stream_name: "0-0"}, count=1, block=1000)
#        messages = self.red.xread({stream_name: "0-0"}).decode('utf-8')
        messages = self.red.xread({stream_name: "0-0"}) # list di bytes
        #print(messages,"\n")
        lastStream={}   
        tstamp=messages[0][1][ind][0]   # bytes
        tstamp=str(tstamp).replace('\"', '') # ci sono delle virgolette in più: le elimino
        
        messages_dict=messages[0][1][ind][1] # dict of bytes
        lastStream[tstamp]={key.decode('utf-8'):messages_dict[key].decode('utf-8') for key in messages_dict.keys()} # dict decoded with utf-8

        #lastStream[tstamp]=json.dumps(messages[0][1][ind][1])   # dict
        #pprint.pp(lastStream)
    
        return(lastStream[tstamp])
                   # esempio: messages[0][1][99][1]['Tensione Cella 1 [V]']
                   # ms_date_timestamp_id=re.search(r'\d+', response.decode("utf-8")).group()
                   # str_timestamp=str(datetime.datetime.fromtimestamp(int(ms_date_timestamp_id)/1000.0))
                   #  messages[0] tutto con il nome del tag redis
                   #  messages[0][0] nome del tag
                   #  messages[0][1] tutto lo stream, ad esempio 100 item
                   #  messages[0][1][n]  ennesimo elemento dello stream, 0 più vecchio 99 più recente
                   #  messages[0][1][n][0]  timestamp ennesimo elemento
                   #  messages[0][1][n][1]  dati ennesimo elemento, è in formato json
    

class DTMinioClient(object):
    """ API per connettersi a ad un DB objetc MinIO e utilizzarne le funzionalità """
    def __init__(self, endpoint="localhost:9000", access_key="4K10mbUN3FxVsDxtDYSh", secret_key="sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD", secure=False ):
        self.config_data_path = CONFIG_DATA_PATH
        """ Path del file di configurazione"""
#        self.configDT = CONFIGDT 
#        self.configDT = readConfig(self.config_data_path, self.configDT)
        self.configDT = CURR_CONFIG
        """ Contenuto del file di configurazione"""

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

        self.client = Minio( endpoint   = self.endpoint,
                             access_key = self.access_key,
                             secret_key = self.secret_key,
                             secure     = self.secure )
        """ Id della connessione al server del client MinIO"""
        
        self.listaconf=""

        logger.info("MINIO: CONNECTED: {minio_host} !!", minio_host=self.endpoint ) 

    def object_exists(self, bucket, obj_path) -> bool:
        """ test esitenza di oggetti salvati nel DB mInio """
        try:
            self.client.stat_object(bucket, obj_path)
            return True
        except S3Error as _:
            return False

    def upload_to_minio(self, local_path,  minio_path, indexFlag=False):
        """ Salva oggetti nel DB Minio """
    #    assert os.path.isdir(local_path)
        for local_file in glob.glob(local_path + '/**'):
            local_file = local_file.replace(os.sep, "/") # Replace \ with / on Windows
            if not os.path.isfile(local_file):
                minio_path_new = minio_path + "/" + os.path.basename(local_file)
                self.upload_to_minio(local_file, minio_path_new)  # è ricorsivo
            else:
                remote_path = os.path.join(minio_path, os.path.basename(local_file))
                remote_path = remote_path.replace(os.sep, "/")  # Replace \ with / on Windows
                self.client.fput_object(self.indexbucket, remote_path, local_file)
        if indexFlag:
            #mm=minio_path+"/"+os.path.basename(INDEXPATHTMP)           
            self.client.fput_object(self.indexbucket, minio_path+"/"+os.path.basename(INDEXPATHTMP), INDEXPATHTMP)

    def download_from_minio(self, minio_path,  dst_local_path):
        """ Scarica oggiti dal DB Minio """
    # for bucket_name in client.list_buckets():
        for item in self.client.list_objects(self.indexbucket, prefix=minio_path, recursive=True):
#        for item in self.client.list_objects(bucket_name, start_after=minio_path, recursive=True):
            full_path = os.path.join( dst_local_path,  item.object_name[len(minio_path):])
#            full_path = os.path.join( dst_local_path,  os.path.basename(item.object_name))
            full_path = full_path.replace(os.sep, "/") # Replace \ with / on Windows
            print(item.object_name)
            self.client.fget_object(self.indexbucket,item.object_name,full_path)

    def deleteFolder_minio(self, bucket_name, minio_path):
        """ cancella oggetti salvati nel DB  Minio """
    # Delete using "remove_objects"
        objects_to_delete = self.client.list_objects(self.indexbucket, prefix=minio_path, recursive=True)
        for obj in objects_to_delete:
            self.client.remove_object(self.indexbucket, obj.object_name)
    
    # def deleteFolder_minio2(self, bucket_name, minio_path):
    # # Delete using "remove_objects"
    #     objects_to_delete = self.client.list_objects(bucket_name, prefix=minio_path, recursive=True)
    #     objects_to_delete = [x.object_name for x in objects_to_delete]
    #     for del_err in self.client.remove_objects(bucket_name, objects_to_delete):
    #         print("Deletion Error: {}".format(del_err))


    def getconflist_minio(self):
        """ Trova nel bucket self.indexbucket tutti gli id delle configurazioni salvate
        Per ogni conf legge il file di indice ( index.jsonId ?) e legge la descrizione, ad es. "conf1" e "descr conf1"
        Ricava la lista che è un dict come stringa di caratteri. ad es: listaconf = '"conf1":"descr conf1", "conf2":"descr conf2","conf3":"descr conf3"' """
        
        self.listaconf = []   # é una lista di liste
        self.listaconf_dict = {}   # é una dict di dict
        for itemC in self.client.list_objects(self.indexbucket, recursive=False):
            #prefisso=item.object_name+"/DTindex.json"
            prefisso=itemC.object_name+DTINDEX
            
            for item in self.client.list_objects(self.indexbucket, prefix=prefisso, recursive=False):
#                print("item=", item.object_name)
                self.client.fget_object(self.indexbucket,item.object_name,INDEXPATHTMP)
                resp=rdfquery(namespace=NAMESPACEDEF,indexpath=INDEXPATHTMP)
#                print(resp)
                self.listaconf.append([resp['name'],resp['description']])
                self.listaconf_dict[resp['name']] = resp

        return (json.dumps(self.listaconf_dict))  # invio un json

    def read_index(self):
        """ Legge il file index.jsonId """
        if  self.object_exists(self.indexbucket, self.indexname):
            findex = open(self.indexname)
            data_index = json.load(findex)
            findex.close()
            return ( data_index )
        else:
            return(None)

    def add_to_index(self, newconf, newdescr):
        """ Aggiunge informazioni della nuova configurazione salavat nel DB Minio nel file index.jsonId """
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
    """ API per connettersi a ad un server InfluxDB e utilizzarne le funzionalità """
    def __init__(self, influx_sim):
        self.config_data_path = CONFIG_DATA_PATH
#        self.configDT = CONFIGDT 
#        self.configDT = readConfig(self.config_data_path, self.configDT)
        self.configDT = CURR_CONFIG
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



#### Definizioni costanti per path nomi file ####
DT_MOSAIK_HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DATA_PATH = DT_MOSAIK_HOME + "/data/"
CONFIGDT_SERVLOCAL_PATH = Path(DT_MOSAIK_HOME+"/configDT_locale.yaml")

if CONFIGDT_SERVLOCAL_PATH.exists():  
    CONFIGDT = "configDT_locale.yaml"
else:
    CONFIGDT = "configDT_MESP.yaml"

EXPERIMENT_CONFIG = "experiment_config.yaml" 
#
CURR_CONFIG = readConfig(CONFIG_DATA_PATH, CONFIGDT)

if "rdf" in CURR_CONFIG:
    NAMESPACEDEF=CURR_CONFIG['rdf']['NAMESPACE']
    DTINDEX=CURR_CONFIG['rdf']['INDEXNAME']
else:
    NAMESPACEDEF="https://www.rse-web.it/" 
    DTINDEX= "DTindex.json"  

INDEXPATHDEF=CONFIG_DATA_PATH+"/"+DTINDEX
INDEXPATHTMP="/tmp"+"/"+DTINDEX
############################################




#### Definizioni costanti e alias ##########
SRC_DTRSE=False  # con false il modello della batteria è locale a dt-rse-mosaik,  con true è quello di DT-rse

S_IDLE    = 'S_IDLE'
S_RUNNING = 'S_RUNNING'
S_READY  = 'S_READY'
S_ENDED  = 'S_ENDED'

S_SIM ='S_SIM'
S_LEARN ='S_LEARN'
S_ON ='1'
S_OFF='0'
DT_ON ='DT_ON'
DT_OFF='DT_OFF'
StrToNum={
        S_OFF  :100,
        S_ON   :111,
        S_SIM  :122,
        S_LEARN:133,
        DT_ON  :140,
        DT_OFF :141
        }

MODSIM = StrToNum[S_SIM]    # era 1
MODLEARN = StrToNum[S_LEARN]  # era 10
NOFORZ =  StrToNum[S_OFF]      # era 0
FORZSIM = MODSIM
FORZLEARN = MODLEARN
STOP = -1

DTHB=2  # tempo di check per heartbeat HB
##########################################