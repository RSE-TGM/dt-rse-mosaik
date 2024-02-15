#!/usr/bin/env python3
#
# Scenario Mosaik con loop MQTT
#
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



def prepScenario(SIM_CONFIG):
    # Create World
    #world = mosaik.World(SIM_CONFIG, time_resolution=0.5)
    world = mosaik.World(SIM_CONFIG, debug=True)   # debug true abilita i grafici dell'andamento della simulazione

    # data load current profile:
    #START = '2023-01-01 01:00:00'
    now = datetime.datetime.now()
    START = f"{now}"
    INPUT_DATA = 'mosaik/configuration/data/input_data.csv' # .csv in your setup

    # Start simulators
    #modelsim = world.start('ModelSim', eid_prefix='Model_',step_size=2.8)
    modelsim = world.start('ModelSim', eid_prefix='Model_')
    collector  = world.start('Collector')

    STARTDATAFILE= '2023-01-01 01:00:00'
    BATTplug = world.start('CSV', sim_start=STARTDATAFILE, datafile=INPUT_DATA)

    DTsdamng= world.start('DTSDA_Mng')

    #INIZTIME= '2024-01-13 17:00:00'
    INIZTIME= START
    influx_sim = world.start('InfluxWriter', step_size=1,   start_date=INIZTIME)

    """ influx_sim = world.start('InfluxWriter',
        step_size=900,
        start_date=START,
    ) """


    # Instantiate models
    #model = examplesim.ExampleModel(init_val=2)
    model   = modelsim.BattModel()
    monitor = collector.Monitor()
    LCUdata = BATTplug.Current.create(1)
    dtsdamng = DTsdamng.DTSDAMng()

    influx = influx_sim.Database(
        url="http://localhost:8086",
        org='RSE',
        bucket='nuovobuck',
        token='aHMudy-R1gicVNWRDzVTWmw4_HPFVCdwzcUTIErKl_i2uVRpCrCpmTOtcOAg0n-qNdnuetSQfTKGHAmgsMeL4A==',
        measurement='experiment_0001'
    )

    # Connect entities
    world.connect(LCUdata[0], model, ('LCU', 'load_current'))
    world.connect(model, monitor, 'load_current', 'output_voltage')
    world.connect(model, influx, 'load_current', 'output_voltage')
    world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
    world.connect(dtsdamng, model, 'DTmode')
    world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')

    return (world, model, dtsdamng)

# Run simulation
#world.set_initial_event(dtsdamng.sid)
#world.run(until=END)
#world.run(until=END,rt_factor=1.1)

def taskRun():
    # run normale, nel processo del thread principale
    world.run(until=END,rt_factor=1.1)

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

        # self.confpath = confpath
        # self.confname = confname
        # self.configDT = readConfig(self.confpath, self.confname)
           
        self.mqttBroker = self.configDT['mqtt']['SERVER']
        self.port = int(self.configDT['mqtt']['PORT'])
        self.user = self.configDT['mqtt']['USER']
        self.passw = self.configDT['mqtt']['PASSWORD']

        # self.mqttBroker = broker
        # self.port = port

        self.client = mqtt.Client(cli)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.username_pw_set(self.user, self.passw)
# connessione al brojer mqtt
        self.client.connect(self.mqttBroker, self.port)

        self.callbacks = self.configDT['mqtt']['DTSDA']['CALLBACK']
        for tag in self.callbacks:
            print(f'{self.callbacks[tag]}')
            self.client.subscribe(self.callbacks[tag])
    
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

        # print("------------------------> DTmqtt_messloop: loop forever")
        # self.client.loop_forever()
        # print("------------------------> DTmqtt_messloop: FINE metodo")
        
        # Connessione a redis
        self.redis = redisDT()
        self.r = self.redis.connect()
        self.redis_tags = self.redis.gettags()
        self.redis.aset('DTSDA_State',S_IDLE) 


    def run(self):
#        while True:    # qui si ritenta la connessione, ma io escludo
#            redisID=self.redis
            try:
                if self.client.loop_forever() != 0:    # invece di self.client.loop()
                    logger.warning('Disconnected from MQTT server: {server}', server=self.mqttBroker)
            except KeyboardInterrupt:
                self.client.disconnect()
#                break
        
    def on_connect(self, mosq, obj, msg, rc): 
        logger.info('Connected to MQTT server: {server}. Wainting for commands...', server=self.mqttBroker)
#        log.info('Connected to MQTT server: %s', self.mqttBroker)
        
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
            world, model, dtsdamng = prepScenario(SIM_CONFIG)
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

    def on_message(self, client, userdata, message):
        # callback per messaggi MQTT
        global world, model, dtsdamng, tRun_on_message
        print(f'------------------------>on_message: Received con topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')

  
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
    global world, model, dtsdamng 
    #carico la configurazione di default
    world, model, dtsdamng = prepScenario(SIM_CONFIG)

    # lancio simulazione
    taskRun()

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
        END=10
        # carico e lancio la configurazione di default
        SIMtest()
    else:
        # modalità normale in "mqtt message loop"
        # connessione a mqtt
        cli_mqtt = DTmqtt()
        
                # climqtt = DTmqtt(
                #     broker="0.0.0.0", 
                #     port=1883, 
                #     cli="DTSDA", 
                #     user="userDT", 
                #     passw="userDT", 
                #     confpath="mosaik/configuration/", 
                #     confname="configDT.yaml")
        
        # Connessione al object DB        
        cli_minio = MinioClient()
       
        cli_mqtt.run()


#-------------------------------------------------------------------------
# inizializzazzione simulazione di test
SIM_CONFIG = {
        'ModelSim': {
            'python': 'batt_simulator:ModelSim',
        },
        'Collector': {
            'python': 'batt_collector:Collector',
        },
        'CSV': {
            'python': 'mosaik_csv:CSV',
        },
        'DTSDA_Mng': {
            'python': 'batt_mng:DTSDA_Mng',
        },
        'InfluxWriter': {
            'python': 'mosaik.components.influxdb2.writer:Simulator',
        },
    }

#END = 20  # 10 seconds
END = 1 * 24 * 60 * 60 # one day in seconds

# Load della simulazine di default
debug=False
####   world, model, dtsdamng = prepScenario(SIM_CONFIG)

# # test per gui
# from PySide6.QtWidgets import QApplication, QWidget
# import sys
# app = QApplication(sys.argv)
# window = QWidget()
# window.show()
# app.exec()

if __name__ == '__main__':
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