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
from batt_simulator import *
from batt_collector import *
from batt_mng import *
from batt_prepscenario import *
#from DT_include import INDEXPATHDEF
from DT_include import *

#from DT_rdf import *

##########################################


def taskRun():
    # run normale, nel processo del thread principale
    #END = 20  # 10 seconds
    END = 1 * 24 * 60 * 60 # one day in seconds
    world.run(until=END,rt_factor=1.1)
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
    while tRun.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e vivo
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
        self.client.username_pw_set(self.user, self.passw)
# connessione al broker mqtt
        self.client.connect(self.mqttBroker, self.port)

        self.callbacks = self.configDT['mqtt']['DTSDA']['CALLBACK']   # lista delle callbacks associate ai comandi mqtt e subscribe degli stessi
        for tag in self.callbacks:
            print(f'{self.callbacks[tag]}')
            self.client.subscribe(self.callbacks[tag])

        self.posts = self.configDT['mqtt']['DTSDA']['POST']
        for tag in self.posts:
            print(f'post da pubblicare: {self.posts[tag]}')
            self.client.subscribe(self.posts[tag])    # eseguo il subcribe comunque perchè le informazioni potrebbero essere generate da altri
                   
        self.misure = self.configDT['mqtt']['DTSDA']['MISURE']['BATT1']
        for tag in self.misure:
            print(f'{self.misure[tag]}')
            self.client.subscribe(self.misure[tag])

# aggiunta delle callback associate ai comandi mqtt
        self.client.message_callback_add(self.callbacks['EndProg'], self.on_EndProg)
        self.client.message_callback_add(self.callbacks['SetModoSIM'], self.on_SetModoSIM)
        self.client.message_callback_add(self.callbacks['SetModoLEARN'], self.on_SetModoLEARN)
        self.client.message_callback_add(self.callbacks['LoadSIM'], self.on_LoadSIM)
        self.client.message_callback_add(self.callbacks['RunSIM'], self.on_RunSIM)
        self.client.message_callback_add(self.callbacks['StopSIM'], self.on_StopSIM)
        self.client.message_callback_add(self.callbacks['PlotGraf'], self.on_PlotGraf)
        self.client.message_callback_add(self.callbacks['LoadConf'], self.on_LoadConf)
        self.client.message_callback_add(self.callbacks['SaveConf'], self.on_SaveConf)
        self.client.message_callback_add(self.callbacks['ListaConfReq'], self.on_ListaConfReq)
        self.client.message_callback_add(self.callbacks['DelConf'], self.on_DelConf)
        self.client.message_callback_add(self.callbacks['CurrConfReq'], self.on_CurrConfReq)
        # print("------------------------> DTmqtt_messloop: loop forever")
        # self.client.loop_forever()
        # print("------------------------> DTmqtt_messloop: FINE metodo")
        
        #-----------------
        # Connessione a redis
        self.redis = redisDT()
        self.r = self.redis.connect()
        self.redis_tags = self.redis.gettags()
        self.redis.aset('DTSDA_State',S_IDLE) 
        #------------------


    def run(self):
#        while True:    # qui si ritenta la connessione, ma io escludo
#            redisID=self.redis
            try:
                if self.client.loop_forever() != 0:    # invece di self.client.loop()
                    logger.warning('Disconnected from MQTT server: {server}', server=self.mqttBroker)
            except KeyboardInterrupt:
                self.client.disconnect()
#                break
    
    def publish(self,tag,message):
        self.client.publish(tag,message)

    def on_message(self, client, userdata, message):
        # callback per echo dei messaggi MQTT
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_message: Received con topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')

    def on_connect(self, mosq, obj, msg, rc): 
        logger.info('Connected to MQTT server: {server}. Wainting for commands...', server=self.mqttBroker)
        
    def disconnect(self):
        return(self.client.loop_stop())
 
    def subscribe(self, topic):
        return(self.client.subscribe(topic))
    
    def on_EndProg(self, client, userdata, message):
        print(f'------------------------>on_EndProg:  DISCONNET and END')
        if self.redis.aget('DTSDA_State') == S_RUNNING :
            self.on_StopSIM(client, userdata, message)
        self.redis.aset('DTSDA_State',S_ENDED) 
        logger.warning('END Request IGNORED. Simulator in state: {state} Stopped! State set to {state2}. EXIT', 
                               state=self.redis.aget('DTSDA_State'), state2=S_IDLE )       
        self.client.disconnect()

    def on_SetModoSIM(self, client, userdata, message):
        print(f'------------------------>on_SetModoSIM:  SetModoSIM')

    def on_SetModoLEARN(self, client, userdata, message):
        print(f'------------------------>on_SetModoLEARN:  SetModoLEARN')

    def on_LoadSIM(self, client, userdata, message):
        global world, model, dtsdamng
        print(f'------------------------>on_LoadSIM:   LOAD DELLA SIMULAZIONE')
        if self.redis.aget('DTSDA_State') == S_IDLE :
            self.redis.aset('DTSDA_State', S_LOADED )
            world, model, dtsdamng = batt_prepScenario()
        else:
            print(f'------------------------>on_LoadSIM:  SIM NOT in IDLE!! ')
            logger.warning('LOAD Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be loaded.', 
                               state=self.redis.aget('DTSDA_State'), state2=S_IDLE ) 


    def on_RunSIM(self, client, userdata, message):
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_RunSIM:  RUN DELLA SIMULAZIONE')
        
        #------------------------------------------
        # Per sopprime il traceback!!!!
        sys.tracebacklimit = 0
        try:
            if self.redis.aget('DTSDA_State') == S_LOADED :
                self.redis.aset('DTSDA_State', S_RUNNING)
                tRun_on_message = taskRunInThread()
            else:
                print(f'------------------------>on_RunSIM:  SIM NOT LOADED!! ')
                logger.warning('RUN Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be run.', 
                               state=self.redis.aget('DTSDA_State'), state2=S_LOADED ) 

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
        print(f'------------------------>on_StopSIM:  Stop della Simulazione')
        try:
            if self.redis.aget('DTSDA_State') == S_RUNNING :
                self.redis.aset('DTSDA_State', S_IDLE)
                world.until = 1
                sleep(1)
                print(f"SHUTDOWN!")    
                world.shutdown()
            else: 
                print(f'------------------------>on_StopSIM:  SIM NOT RUNNING!! ')
                logger.warning('STOP Request IGNORED. Simulator in state: {state} NOT changed! Simulator must be {state2} to be stopped.', 
                               state=self.redis.aget('DTSDA_State'), state2=S_RUNNING ) 

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
        source_path = CONFIG_DATA_PATH
        minio_path = str(message.payload.decode("utf-8")) # il message.payload é un str formattata come un dict del tipo {nome:descrizione}. Ad es:  '{"conf1":"descrizione conf1"}'
        if not minio_path:
            minio_path='confX'

        # converto da str a dict
        minio_path_dict= json.loads(minio_path)

        for key, value in minio_path_dict.items():
#            print( key, value)
            rdfcreate(indexpath=INDEXPATHTMP, name=key, description=value)
            logger.info("Salvataggio configurazione da {source_path} nel objDB con id {minio_path} ", source_path=source_path, minio_path=minio_path )
            cli_minio.upload_to_minio(local_path=source_path,  minio_path=key)
            # a questo punto copio solo index.json giusto, prodotto nella directory /tmp (con indexFlag a true)
            cli_minio.upload_to_minio(local_path=INDEXPATHTMP,  minio_path=key, indexFlag=True)
          
    def on_LoadConf(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_LoadConf: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
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

    
    def on_ListaConfReq(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_ListaConfReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        id_minio_path='conf'
        listaconf =  str(cli_minio.getconflist_minio())   # variabile di tipo text
        self.client.publish(self.posts['listaconf'],listaconf)        
        print(f'------------------------>on_ListaConfReq: nuova listaconf: {listaconf} pubblicata')

    def on_DelConf(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_deleteFolder_minio: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        minio_path = str(message.payload.decode("utf-8"))
        logger.info("Rimozione configurazione {minio_path} dal bucket {bucket_name}", minio_path=minio_path, bucket_name=cli_minio.indexbucket)
        cli_minio.deleteFolder_minio(bucket_name=cli_minio.indexbucket, minio_path=minio_path)

    def on_CurrConfReq(self, client, userdata, message):
        global cli_minio
        print(f'------------------------>on_CurrConfReq: Received with topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
        confActual=rdfquery(indexpath=INDEXPATHDEF)  # è un dict
        currconf = json.dumps(confActual) # converto in json per inviare
        ## currconf=str(confActual)
        nameActual=confActual['name']
        descrActual=confActual['description']

        #id_minio_path='conf'
        # si deve leggere il file index nella directory 'configurazione" dell'app ... per ora ci metto una stringa fissa
#        currconf =  '"currconf": "Questa è la descrizione della configurazione"'  # variabile di tipo text
        self.client.publish(self.posts['currconf'], currconf)        
        print(f'------------------------>on_CurrConfReq: currconf: {currconf} pubblicata')


  
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
    

def SIMtest():
    #
    # Viene eseguito un transitorio in batch e visulaizzati i plot di prestazione       
    #
    global world, model, dtsdamng , debug

    #carico la configurazione di default
    world, model, dtsdamng = batt_prepScenario()

    # lancio simulazione
    #taskRun()
    debug=True
    END=10
    world.run(until=END,rt_factor=1.1)

    ## grafici attivati con il debug mode
    mosaik.util.plot_dataflow_graph(world, folder='util_figures')
    mosaik.util.plot_execution_graph(world, folder='util_figures')
    mosaik.util.plot_execution_time(world, folder='util_figures')
    mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
        

def main():
    global END, cli_minio
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        print(f'Modalità TEST, {args.test}!')       
# carico e lancio la configurazione di default
        SIMtest()
    else:
# modalità normale in "mqtt message loop"
        # Connessione a mqtt e sua configurazione, la classe si connette inoltre a Redis. 
        # Invece il modello della batteria ( modulo batt_prepscenario ) si connette direttamente a InfluxDB
        cli_mqtt = DTmqtt()

        ## Connessione al object DB Minio      
        cli_minio = DTMinioClient()
        
        # eseguo il backup della configurazione iniziale ...
        confActual=rdfquery(indexpath=INDEXPATHDEF)

        adesso=datetime.datetime.now()
        confbackName='CurrConfBackup'+adesso.strftime("-%d%m%Y-%H_%M_%S_%f") 
        descrActual=confActual['description']
        confback = f"""{{"{confbackName}":"{descrActual}"}}"""
        cli_mqtt.publish(cli_mqtt.callbacks['SaveConf'], confback)

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
