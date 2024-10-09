#!/usr/bin/env python3
#
# Scenario Mosaik con loop MQTT
#
########################################
import sys
import argparse
from time import sleep, perf_counter
# import logging as log
from loguru import logger

import mosaik
import mosaik_api_v3 as mosaik_api
#from mosaik.util import connect_randomly, connect_many_to_one
from mosaik.util import *
#import mosaik.scheduler as scheduler

from threading import Thread
#import asyncio
# import nest_asyncio
# #        call apply()
# nest_asyncio.apply()
import paho.mqtt.client as mqtt

##### import packages locali
from batt_model import *
from DT_collector import *
from batt_mng import *
from DT_prepscenario import *
#from DT_include import INDEXPATHDEF
from DT_include import *

#from DT_rdf import *

##########################################


def taskRun():
    # run normale, nel processo del thread principale
    #END = 20  # 10 seconds
    END = 1 * 24 * 60 * 60 # one day in seconds
    world.run(until=END,rt_factor=1.)
    # Run simulation
    #world.set_initial_event(dtsdamng.sid)
    #world.run(until=END)
    #world.run(until=END,rt_factor=1.1)

def taskRunInThread_and_time_check(): 
    # apertura di un thread figlio e run nel nuovo thread e check per essere fermto dopo tre iterazioni
    tRun = Thread(target=taskRun)
    tRun.start()
    sleep(1)

    tRun.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
    i=0
    while tRun.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e' vivo
        print(f"-----CHECK-TIMEOUT---Simulazione in RUN-{world.tqdm.total}------------------------------------------------------------------------------------------------------------>")
        tRun.join(timeout=1)  # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop
        if i > 3: 
            world.until = 1  # fermo (brutalmente) la simulazione dopo 3 iterazioni
            
            print(f"Fermo tutto i={i}")
        i=i+1

def taskRunInThread(): 
    # apertura di un thread figlio e run nel nuovo thread, non apsetto la fine del nuovo thread 
    tRun = Thread(target=taskRun)
    tRun.start()
    sleep(1)
    return tRun

def heartbeat(dtime=1, cliMQTT=None, cliRedis=None): 
    # thread per il check periodico di esistenza in vita del digital twin, ogni DTHB secondi scrive su redis lo stato DTHBstate
    # apertura di un thread figlio e run nel nuovo thread, non apsetto la fine del nuovo thread 
    
    def hb(dtime,cliMQTT):
        n=0
        logger.info('Eccomi:  iter={n} Wainting ...{dtime} seconds', n=n, dtime=dtime)
        while True:
            n=n+1
#            logger.info('Eccomi:  iter={n} Wainting ...{dtime} seconds', n=n, dtime=dtime)
            cliRedis.aset('DTHBstate', DT_OFF, hmode=True)
            if cliMQTT.is_connected():
                cliRedis.aset('DTHBstate', DT_ON, hmode=True)
                sleep(dtime)
            else:
                exit()

    thHB = Thread(target=hb(dtime,cliMQTT))
    thHB.start()
    return thHB

# async def do_stuff(i):
#     ran = random.uniform(0.1, 0.5)
#     await asyncio.sleep(ran)  # NOTE if we hadn't called
#     # asyncio.set_event_loop() earlier, we would have to pass an event
#     # loop to this function explicitly.
#     print(i, ran)
#     return ran


# def thr(i):
#     # we need to create a new loop for the thread, and set it as the 'default'
#     # loop that will be returned by calls to asyncio.get_event_loop() from this
#     # thread.
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     ret = loop.run_until_complete(do_stuff(i))
#     loop.close()
#     return ret
## sys.exit()



class DTmqtt(object):
    def __init__(self, broker="0.0.0.0", port=1883, cli="DTSDA", user="userDT", passw="userDT", confpath="mosaik/configuration/", confname="configDT.yaml" ):

# lettura del file di configurazione per acquisire le tag mqtt
        self.config_data_path = CONFIG_DATA_PATH
        self.configDT = CONFIGDT
        self.configDT = readConfig(self.config_data_path, self.configDT)

           
        self.mqttBroker = self.configDT['mqtt']['SERVER']
        self.port = int(self.configDT['mqtt']['PORT'])
        self.user = self.configDT['mqtt']['USER']
        self.passw = self.configDT['mqtt']['PASSWORD']


        self.client = mqtt.Client(cli)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.user, self.passw)
# connessione al broker mqtt
        self.client.connect(self.mqttBroker, self.port)

        self.callbacks = self.configDT['mqtt']['DTSDA']['CALLBACK']   # lista delle callbacks associate ai comandi mqtt e subscribe degli stessi
        for tag in self.callbacks:
            print(f'{self.callbacks[tag]}')
            self.client.subscribe(self.callbacks[tag])

        # self.command = self.configDT['mqtt']['DTSDA']['COMMAND']   # lista delle callbacks associate ai comandi mqtt e subscribe degli stessi
        # for tag in self.command:
        #     print(f'{self.command[tag]}')
        #     self.client.subscribe(self.command[tag])

        self.posts = self.configDT['mqtt']['DTSDA']['POST']
        for tag in self.posts:
            print(f'post da pubblicare: {self.posts[tag]}')
            self.client.subscribe(self.posts[tag])    # eseguo il subcribe comunque perchè le informazioni potrebbero essere generate da altri
                   
        # self.posts2 = self.configDT['mqtt']['DTSDA']['POST2']
        # for tag in self.posts2:
        #     print(f'post da pubblicare: {self.posts2[tag]}')
        #     self.client.subscribe(self.posts2[tag])    # eseguo il subcribe comunque perchè le informazioni potrebbero essere generate da altri
                   
        self.misure = self.configDT['mqtt']['DTSDA']['MISURE']['BATT1']
        for tag in self.misure:
            print(f'{self.misure[tag]}')
            self.client.subscribe(self.misure[tag])

# aggiunta delle callback associate ai comandi mqtt
##        self.client.message_callback_add(self.callbacks['MainCall'], self.on_switch)

        self.client.message_callback_add(self.callbacks['EndProg'], self.on_EndProg)
        self.client.message_callback_add(self.callbacks['SetModoSIM'], self.on_SetModoSIM)
        self.client.message_callback_add(self.callbacks['SetModoLEARN'], self.on_SetModoLEARN)
        self.client.message_callback_add(self.callbacks['InitSIM'], self.on_InitSIM)
        self.client.message_callback_add(self.callbacks['RunSIM'], self.on_RunSIM)
        self.client.message_callback_add(self.callbacks['StopSIM'], self.on_StopSIM)
        self.client.message_callback_add(self.callbacks['PlotGraf'], self.on_PlotGraf)
        self.client.message_callback_add(self.callbacks['LoadConf'], self.on_LoadConf)
        self.client.message_callback_add(self.callbacks['SaveConf'], self.on_SaveConf)
        self.client.message_callback_add(self.callbacks['ListaConfReq'], self.on_ListaConfReq)
        self.client.message_callback_add(self.callbacks['DelConf'], self.on_DelConf)
        self.client.message_callback_add(self.callbacks['CurrConfReq'], self.on_CurrConfReq)
        self.client.message_callback_add(self.callbacks['StatusReq'], self.on_StatusReq)
        self.client.message_callback_add(self.callbacks['HealthReq'], self.on_HealthReq)
        # print("------------------------> DTmqtt_messloop: loop forever")
        # self.client.loop_forever()
        # print("------------------------> DTmqtt_messloop: FINE metodo")
        
        #-----------------
        # Connessione a redis
        self.redis = redisDT()
        self.r = self.redis.connect()
        #self.redis_tags = self.redis.gettags()
        self.redis.aset('DTSDA_State',S_IDLE, hmode=True) 
        #------------------


    def run(self):
#        while True:    # qui si ritenta la connessione, ma io escludo
#            redisID=self.redis
           
        try:
            self.client.loop_start()   # invece di self.client.loop()
            heartbeat(dtime=DTHB, cliMQTT=self.client, cliRedis= self.redis) # attiva in redis lo stato di DT funzionante DTHBstate, il tempo di check è DTHB
            logger.warning('-------------> dopo heartbeat: {server}', server=self.mqttBroker)
        except KeyboardInterrupt:
            logger.warning('-------------> disconnessione da MQTT per ctr-C! server: {server}', server=self.mqttBroker)
            self.client.disconnect()
        

# vecchia versione senza herat beat, funzionanate !!
    def run_noHB(self):
#        while True:    # qui si ritenta la connessione, ma io escludo
#            redisID=self.redis
            logger.warning('-------------> dopo heartbeat: {server}', server=self.mqttBroker)
            try:
                if self.client.loop_forever() != 0:    # invece di self.client.loop()
                    logger.warning('Disconnected from MQTT server: {server}', server=self.mqttBroker)
            except KeyboardInterrupt:
                self.client.disconnect()
#                break



    def on_connect(self, mosq, obj, msg, rc):
        logger.info('Connected to MQTT server: {server}. Wainting for commands...', server=self.mqttBroker)
        
    def on_disconnect(self, userdata, reason_code, properties):
        self.redis.aset('DTHBstate', DT_OFF, hmode=True)
        return(self.client.loop_stop(force=True))
    
    def subscribe(self, topic):
        return(self.client.subscribe(topic))
    
    def publish(self,tag,message):
        self.client.publish(tag,message)

    def on_message(self, client, userdata, message):
        # callback per echo dei messaggi MQTT
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_message: Received con topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')

    # def on_switch(self, client, userdata, message):
    #     payl=json.loads(message.payload.decode("utf-8"))
    #     if payl['command'] == self.command['EndProg'] :
    #         self.on_EndProg(client, userdata, message)
    #     elif payl['command'] == self.command['SetModoSIM'] :
    #         self.on_SetModoSIM(client, userdata, message)
    #     elif payl['command'] == self.command['SetModoLEARN'] :
    #         self.on_SetModoLEARN(client, userdata, message)
    #     elif payl['command'] ==  self.command['InitSIM'] :
    #         self.on_InitSIM(client, userdata, message)
    #     elif payl['command'] == self.command['RunSIM'] :
    #         self.on_RunSIM(client, userdata, message)
    #     elif payl['command'] == self.command['StopSIM'] :
    #         self.on_StopSIM(client, userdata, message)
    #     elif payl['command'] == self.command['PlotGraf'] :
    #         self.on_PlotGraf(client, userdata, message)
    #     elif payl['command'] == self.command['ListaConfReq'] :
    #         userdata = 1    # per abilitare la modalià con topic DTSDA + comando in payload
    #         self.on_ListaConfReq(client, userdata, message)
    #     elif payl['command'] == self.command['LoadConf'] :
    #         userdata = 1    # per abilitare la modalià con topic DTSDA + comando in payload
    #         self.on_LoadConf(client, userdata, message)
    #     elif payl['command'] == self.command['SaveConf'] :
    #         userdata = 1     # per abilitare la modalià con topic DTSDA + comando in payload
    #         self.on_SaveConf(client, userdata, message)
    #     elif payl['command'] == self.command['DelConf'] :
    #         userdata = 1    # per abilitare la modalià con topic DTSDA + comando in payload
    #         self.on_DelConf(client, userdata, message)
    #     elif payl['command'] == self.command['CurrConfReq'] :
    #         userdata = 1    # per abilitare la modalià con topic DTSDA + comando in payload
    #         self.on_CurrConfReq(client, userdata, message)

    

    def on_EndProg(self, client, userdata, message):
        print(f'------------------------>on_EndProg:  DISCONNET and END')
        if self.redis.aget('DTSDA_State', hmode=True) == S_RUNNING :
            self.on_StopSIM(client, userdata, message)

        if (self.redis.aget('DTSDA_State', hmode=True) == S_IDLE) or (self.redis.aget('DTSDA_State', hmode=True) == S_READY): 
            self.redis.aset('DTSDA_State',S_ENDED, hmode=True)     
            self.client.disconnect()
        else:
            logger.warning('END Request IGNORED. Simulator in state: {state} Stopped! State must be {state2} to end', 
                               state=self.redis.aget('DTSDA_State', hmode=True), state2=S_IDLE )   


    def on_SetModoSIM(self, client, userdata, message):
        print(f'------------------------>on_SetModoSIM:  SetModoSIM')
        self.redis.aset('DTmode', S_SIM, hmode=True)
        self.redis.aset('DTmode_set', S_SIM, hmode=True)

    def on_SetModoLEARN(self, client, userdata, message):
        print(f'------------------------>on_SetModoLEARN:  SetModoLEARN')
        self.redis.aset('DTmode', S_LEARN, hmode=True)
        self.redis.aset('DTmode_set', S_LEARN, hmode=True)


    def on_InitSIM(self, client, userdata, message):
        global world, model, dtsdamng
        print(f'------------------------>on_InitSIM:   INIT DELLA SIMULAZIONE')
        if self.redis.aget('DTSDA_State', hmode=True) == S_IDLE :
            self.redis.aset('DTSDA_State', S_READY , hmode=True)
            world, model, dtsdamng = DT_prepScenario()
        else:
            print(f'------------------------>on_InitSIM:  SIM NOT in IDLE!! ')
            logger.warning('LOAD Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be loaded.', 
                               state=self.redis.aget('DTSDA_State', hmode=True), state2=S_IDLE ) 


    def on_RunSIM(self, client, userdata, message):
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_RunSIM:  RUN DELLA SIMULAZIONE')
        
        #------------------------------------------
        # Per sopprime il traceback!!!!
        sys.tracebacklimit = 0
        try:
            if self.redis.aget('DTSDA_State', hmode=True) == S_READY :
                self.redis.aset('DTSDA_State', S_RUNNING, hmode=True)
                tRun_on_message = taskRunInThread()
            else:
                print(f'------------------------>on_RunSIM:  SIM NOT READY, Must be inizialized to run a simulation!! ')
                logger.warning('RUN Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be run.', 
                               state=self.redis.aget('DTSDA_State', hmode=True), state2=S_READY ) 

        except Exception as e:
            if debug:
                raise # re-raise the exception
                      # traceback gets printed
            else:
                print("{}: {}".format(type(e).__name__, e))
        sys.tracebacklimit = 1
        # FINE soppressione traceback!!!!
        #-----------------------------------------

    def on_StopSIM(self, client, userdata, message):
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_StopSIM:  Simulation STOP request')
        try:
            if (self.redis.aget('DTSDA_State', hmode=True) == S_RUNNING) or (self.redis.aget('DTSDA_State', hmode=True) == S_READY):  
                print(f'------------------------>on_StopSIM:  Exec STOP of the Simulation...')  
                self.redis.aset('DTSDA_State', S_IDLE, hmode=True)           
                world.until = 1
                sleep(1)
                print(f"SHUTDOWN!")    
                world.shutdown()
                
                print(f'------------------------>on_StopSIM:  STOP of the Simulation!')
            else: 
                print(f'------------------------>on_StopSIM:  SIM NOT RUNNING or READY to be stopped! ')
                logger.warning('STOP Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be stopped.', 
                               state=self.redis.aget('DTSDA_State', hmode=True), state2=S_RUNNING ) 

        except Exception as e:
            if debug:
                raise # re-raise the exception, traceback gets printed                 
            else:
                print("{}: {}".format(type(e).__name__, e))

    def on_PlotGraf(self, client, userdata, message):
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_PlotGraf:  PLOTGRAF per Debug')
        ## grafici attivati con il debug mode
        mosaik.util.plot_dataflow_graph(world, folder='util_figures')
        mosaik.util.plot_execution_graph(world, folder='util_figures')
        mosaik.util.plot_execution_time(world, folder='util_figures')
        mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
    
    def on_SaveConf(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_SaveConf: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        if self.redis.aget('DTSDA_State', hmode=True) != S_IDLE :
            print(f'------------------------>on_SaveConf:   NOT in IDLE!! ')
            logger.warning('SAVE Request IGNORED. DTwin in state: {state} NOT changed!  must be {state2} to save a configuration', 
                               state=self.redis.aget('DTSDA_State', hmode=True), state2=S_IDLE ) 
            return

        source_path = CONFIG_DATA_PATH
        userdata=1
        if userdata == 1:
                payl=json.loads(message.payload.decode("utf-8")) 
                minio_path_dict= {}
                minio_path = payl['id']
                minio_path_dict[minio_path]= payl['description']
        else:
            minio_path = str(message.payload.decode("utf-8")) # il message.payload é un str formattata come un dict del tipo {nome:descrizione}. Ad es:  '{"conf1":"descrizione conf1"}'
            # converto da str a dict
            minio_path_dict= json.loads(minio_path)
        
        
        if not minio_path:
            minio_path='confX'
            minio_path_dict= json.loads(minio_path)


        #  produco DTindex.json che identifica univocamente la configurazione
        rdfcreate(indexpath=INDEXPATHTMP, name=minio_path, description=minio_path_dict[minio_path])
        logger.info("Salvataggio configurazione da {source_path} nel objDB con id {minio_path} ", source_path=source_path, minio_path=minio_path )
        cli_minio.upload_to_minio(local_path=source_path,  minio_path=minio_path)
        # a questo punto copio solo DTindex.json giusto, prodotto nella directory /tmp (con indexFlag a true)
        cli_minio.upload_to_minio(local_path=INDEXPATHTMP,  minio_path=minio_path, indexFlag=True)

#         for key, value in minio_path_dict.items():
# #            print( key, value)
#             rdfcreate(indexpath=INDEXPATHTMP, name=key, description=value)
#             logger.info("Salvataggio configurazione da {source_path} nel objDB con id {minio_path} ", source_path=source_path, minio_path=minio_path )
#             cli_minio.upload_to_minio(local_path=source_path,  minio_path=key)
#             # a questo punto copio solo index.json giusto, prodotto nella directory /tmp (con indexFlag a true)
#             cli_minio.upload_to_minio(local_path=INDEXPATHTMP,  minio_path=key, indexFlag=True)
          
    def on_LoadConf(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_LoadConf: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        if self.redis.aget('DTSDA_State', hmode=True) != S_IDLE :
            print(f'------------------------>on_LoadConf:   NOT in IDLE!! ')
            logger.warning('LOAD Request IGNORED. DTwin in state: {state} NOT changed!  must be {state2} to load a configuration', state=self.redis.aget('DTSDA_State', hmode=True), state2=S_IDLE ) 
            return
        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8")) 
            minio_path = payl['id'] +'/'
            pass
        else:
            minio_path = str(message.payload.decode("utf-8")) +'/'  # E' una str. Ad es: 'conf1'. Aggiungo la barra se no va in crash, 
        
        if not minio_path:
            minio_path='confX/'

        dst_local_directory = CONFIG_DATA_PATH

        cli_minio.download_from_minio( minio_path=minio_path, dst_local_path=dst_local_directory)
        confActual=rdfquery(indexpath=INDEXPATHDEF)  # è un dict
        nameActual=confActual['name']
        descrActual=confActual['description']

        # logger.info("Carico configurazione dal objDB con id {minio_path} in {dst_local_directory} ", minio_path=minio_path, dst_local_directory=dst_local_directory )
        logger.info("Caricata la configurazione dal objDB  {nameActual}:{descrActual} in {dst_local_directory}", nameActual=nameActual, descrActual=descrActual, dst_local_directory=dst_local_directory)

    def on_DelConf(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_deleteFolder_minio: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        # if self.redis.aget('DTSDA_State') != S_IDLE :
        #     print(f'------------------------>on_DelConf:   NOT in IDLE!! ')
        #     logger.warning('Delete Request IGNORED. DTwin in state: {state} NOT changed!  must be {state2} to delete a configuration', state=self.redis.aget('DTSDA_State'), state2=S_IDLE ) 
        #     return
        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8")) 
            minio_path = payl['id']
        else:
            minio_path = str(message.payload.decode("utf-8"))
        
        logger.info("Rimozione configurazione {minio_path} dal bucket {bucket_name}", minio_path=minio_path, bucket_name=cli_minio.indexbucket)
        cli_minio.deleteFolder_minio(bucket_name=cli_minio.indexbucket, minio_path=minio_path)

    
    def on_ListaConfReq(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_ListaConfReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        id_minio_path='conf'
        listaconf =  str(cli_minio.getconflist_minio())   # variabile di tipo text

        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8"))    # converte in dict
        else:
            payl={}
            payl['id']="uidx"

        listaconf_dict={}
        listaconf_dict['command'] = self.posts['listaconf']
        listaconf_dict['id'] = payl['id']
        listaconf_dict['description'] = listaconf

        
        self.client.publish(self.posts['listaconf'],json.dumps(listaconf_dict))       
#        self.client.publish(self.posts['listaconf'],listaconf)        
        print(f'------------------------>on_ListaConfReq: nuova listaconf: {listaconf} pubblicata')

    def on_CurrConfReq(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_CurrConfReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        confActual=rdfquery(indexpath=INDEXPATHDEF)  # è un dict
       # currconf = json.dumps(confActual) # converto in json per inviare
        ## currconf=str(confActual)
        nameActual=confActual['name']
        descrActual=confActual['description']
        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8"))
        else:
            payl={}
            payl['id']="uidx"

        #id_minio_path='conf'
        # si deve leggere il file index nella directory 'configurazione" dell'app ... per ora ci metto una stringa fissa
#        currconf =  '"currconf": "Questa è la descrizione della configurazione"'  # variabile di tipo text
        currconf_dict={}
        currconf_dict['command']=self.posts['currconf']
        currconf_dict['id']=payl['id']
        currconf_dict['description'] = confActual
        self.client.publish(self.posts['currconf'], json.dumps(currconf_dict))
#        self.client.publish(self.posts['currconf'], currconf)

        print(f'------------------------>on_CurrConfReq: currconf: {confActual} pubblicata')

    def on_StatusReq(self, client, userdata, message):
        print(f'------------------------>on_StatusReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        
        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8"))    # converte in dict
        else:
            payl={}
            payl['id']="uidx"

        status_dict = {}
        status_dict = self.r.hgetall(' '.join(self.configDT['redis']['htags']))
        status_dict = {key.decode('utf-8'):value.decode('utf-8') for key,value in status_dict.items()}  # elimino il b'...
       #  status =json.dumps(status_dict) # converto in json per inviare
        
        statusRefBatt_dict ={}
        tagg=self.configDT['redis']['batt1']['RefBattDIM']
        ind=int(self.redis.red.get(tagg).decode('utf-8'))-1
        #ind= self.r.aget(self.configDT['redis']['batt1']['RefBattDIM'])-1  # dato più recente
        statusRefBatt_dict = self.redis.readstream(self.configDT['redis']['batt1']['RefBatt'], ind)


        currstatus_dict = {}
        currstatus_dict['command']=self.posts['status']
        currstatus_dict['id']=payl['id']
        currstatus_dict['status'] = status_dict
        currstatus_dict['statusRefBatt'] = statusRefBatt_dict

        self.client.publish(self.posts['status'],json.dumps(currstatus_dict))   

    def on_HealthReq(self, client, userdata, message):
        print(f'------------------------>on_HealthReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        
        userdata=1
        if userdata == 1:
            payl=json.loads(message.payload.decode("utf-8"))    # converte in dict
        else:
            payl={}
            payl['id']="uidx"

        currstatus_dict = {}
        currstatus_dict['command']=self.posts['health']
        currstatus_dict['id']=payl['id']
        currstatus_dict['description'] = self.callbacks['MainCall']+" is ALIVE"

        self.client.publish(self.posts['health'],json.dumps(currstatus_dict))   

  
def CheckForTmaxLoop(world, model, dtsdamng, tRun, TMAX):
#    DTmqtt_messloop()                                                                                                                                                                                                                                                                                                                                        c
    tRun.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
    while tRun.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e vivo
#        tcurrent=model.sim.last_step*world.time_resolution
        tcurrent=world.sims['ModelSim-0'].last_step.time*world.time_resolution
        print(f"-----CHECK-TIMEOUT---Simulazione in RUN al secondo={tcurrent} di {world.until}-------{world.tqdm}--------------------------------------------------------------------------------->")
        if tcurrent > TMAX: 
            world.until = 1  # fermo (brutalmente) la simulazione
            #world.shutdown()
            print(f"Fermo tutto al passo={world.sims['ModelSim-0'].last_step.time}")
           
        tRun.join(timeout=1)  # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop
 
def CheckForTmax(world, model, dtsdamng, tRun, TMAX):
    # tRun.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
    if tRun.is_alive():   # se il thread è vivo, vuol dire che non ha finito
#        tcurrent=model.sim.last_step*world.time_resolution
        tcurrent=world.sims['ModelSim-0'].last_step.time*world.time_resolution
        print(f"-----CHECK-TIMEOUT---Simulazione in RUN al secondo={tcurrent} di {world.until}-------{world.tqdm}--------------------------------------------------------------------------------->")
        if tcurrent > TMAX: 
            world.until = 1  # fermo (brutalmente) la simulazione
            #world.shutdown()
            print(f"Fermo tutto al passo={world.sims['ModelSim-0'].last_step.time}")
            return True
        else:
            return False
    else:
        return False
    

def SIMtest( tfin, plotfig=False, rt_factor=1.):
    #
    # Viene eseguito un transitorio in batch e visulaizzati i plot di prestazione       
    #
    global world, model, dtsdamng , debug

    #carico la configurazione di default
    world, model, dtsdamng = DT_prepScenario()

    # lancio simulazione
    #taskRun()
    debug=True
    END=tfin
        # rt_passed = perf_counter() - rt_start
    
    RunInizTime=perf_counter()
    #rt_factor=1.  così la simulazione è in tempo reale. Ad esempio con 0.1 rimane in passo; In 1 secondo produce 10 passi di 1 secondo di step di integrazione, cioè 10 volte il tempo reale, test fatto con END=200
    #logger.disable("mosaik.scheduler")
    world.run(until=END,rt_factor=rt_factor)
    RunEndTime=perf_counter()
    print(f'rt_factor={rt_factor} END={END} rt_time forcast={rt_factor*END}')
    print(f'RunEndTime={RunEndTime} RunInizTime={RunInizTime} rt_time={RunEndTime-RunInizTime}')
        # until: int,
        # rt_factor: Optional[float] = None,
        # rt_strict: bool = False,
        # print_progress: Union[bool, Literal["individual"]] = True,
        # lazy_stepping: bool = True,

    if plotfig:
    ## grafici attivati con il debug mode
        mosaik.util.plot_dataflow_graph (world, folder='util_figures')
        mosaik.util.plot_execution_graph(world, folder='util_figures')
        mosaik.util.plot_execution_time (world, folder='util_figures')
        mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
        

def main():
    global cli_minio
    parser = argparse.ArgumentParser()
    parser.add_argument('-test', action='store_true', help="Modalità test. Esegue una simulazione in batch (durata di default 10 secondi) e termina")
    parser.add_argument('-rt_factor', help="rapporto tempoSimulazione/tempoReale")
    parser.add_argument('-tfin', help="Durata della simulazione nella modalità test")
    parser.add_argument('-plot', action='store_true', help="In modalità test, stampa grafi di debug")

    args = parser.parse_args()

    # disablito il wanring sul passo di tempo 
    logger.disable("mosaik.scheduler")
    if args.test:        
#
# Modalità test
#        
        if args.tfin:
            END=int(args.tfin)
            print(f'Modalità TEST, {args.test}, t fine simulazione: {args.tfin}!') 
        else:
            # run test, durata di default 10 secondi
            END=10
            print(f'Modalità TEST, {args.test} , t fine simulazione: {END}!')
        
        if args.plot: plotfig=True 
        else: plotfig=False
    
        if args.rt_factor : rt_factor=float(args.rt_factor)
        else:  rt_factor=1.

        SIMtest(END, plotfig=plotfig, rt_factor=rt_factor)
    else:
#
# Modalità normale in "mqtt message loop"
#
        # Connessione a mqtt e sua configurazione. La classe DTmqtt si connette anche a Redis. 
        # Invece il modello della batteria ( modulo DT_prepscenario ) si connette direttamente a InfluxDB
        cli_mqtt = DTmqtt()

        ## Connessione al object DB Minio      
        cli_minio = DTMinioClient()
        

####### Eseguo il backup della configurazione iniziale ...
        confActual=rdfquery(indexpath=INDEXPATHDEF)
        adesso=datetime.datetime.now(pytz.timezone(TZONE))
        confbackName='CurrConfBackup'+adesso.strftime("-%d%m%Y-%H_%M_%S_%f") 
        descrActual=confActual['description']
        idActual=confActual['date']
        commandActual='Currconf init'
        payl = f"""{{"command":"{commandActual}", "id":"{confbackName}", "description":"{descrActual}"}}"""
        cli_mqtt.publish(cli_mqtt.callbacks['SaveConf'], payl)
######


        ## lancio del loop senza fine mqtt   
        cli_mqtt.run()

# # test per gui
# from PySide6.QtWidgets import QApplication, QWidget
# import sys
# app = QApplication(sys.argv)
# window = QWidget()
# window.show()
# app.exec()

if __name__ == '__main__':
    debug=False
    main()

####
# TMAX=3000  # fermo la simulazione dopo TMAX secondi
# try:
#     CheckForTmaxLoop(world, model, dtsdamng, tRun, TMAX)
# except Exception as e:
#     if debug:
#         raise # re-raise the exception
#               # traceback gets printed
#     else:
#         print("{}: {}".format(type(e).__name__, e))
# sleep(1)
#####
# Esempio accesso a variabili del simulatore:
# world.sims['ModelSim-0']._proxy.sim.entities['Model_0'].load_current
# world.sims['ModelSim-0'].output_to_push[('Model_0', 'DTmode_set')][0][1]  ritorna il valore di DTmode_set
# world.sims['ModelSim-0'].current_step.time         tempo corrente della task ModelSim-0
#####
