#
# Scanario Mosaik con loop MQTT
#
import sys
import argparse
from time import sleep, perf_counter

import mosaik
import mosaik_api_v3 as mosaik_api
#from mosaik.util import connect_randomly, connect_many_to_one
from mosaik.util import *
from batt_simulator import *
from batt_collector import *
from batt_mng import *

#import asyncio
#import mosaik.scheduler as scheduler
from threading import Thread
# import nest_asyncio
# #        call apply()
# nest_asyncio.apply()

import paho.mqtt.client as mqtt


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
    world.run(until=END,rt_factor=1.1)

def taskRunInThread1(): 
    tRun = Thread(target=taskRun)
    tRun.start()
    sleep(1)

    tRun.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
    i=0
    while tRun.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e vivo
        print(f"-----CHECK-TIMEOUT---Simulazione in RUN-{world.tqdm.total}------------------------------------------------------------------------------------------------------------>")
        tRun.join(timeout=1)  # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop
        if i > 3: 
            world.until = 1  # fermo (brutalmente) la simulazione
            
            print(f"Fermo tutto i={i}")
        i=i+1

def taskRunInThread2(): 
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

class DTmqtt:
    def __init__(self, name, mqttBroker, user, passwd, on_message):
        self.mqttBroker = mqttBroker
        self.client = mqtt.Client(name)
        self.client.on_message = on_message
        self.client.username_pw_set(user, passwd)

    def connect(self):
        ret= self.client.connect(self.mqttBroker)
        self.client.loop_start()
        return(ret)
 
    def disconnect(self):
        return(self.client.loop_stop())

 
    def subscribe(self, topic):
        return(self.client.subscribe(topic))
    



def DTmqtt_messloop():   
#    mqttBroker = "mqtt.eclipseprojects.io"   # mqtt brocker free di prova
    mqttBroker = "0.0.0.0"     # mqtt brocker in localhost
    client = mqtt.Client("DTSDA")
    client.on_message = on_message  # callback dei messaggi
    client.username_pw_set("userDT", "userDT")

    ret = client.connect(mqttBroker)

    client.subscribe("DTSDA/temperatura")
    client.subscribe("DTSDA/tensione")
    client.subscribe("DTSDA/corrente")
    client.subscribe("DTSDA/SIM")
    client.subscribe("DTSDA/LEARN")
    client.subscribe("DTSDA/RUNSIM")
    client.subscribe("DTSDA/STOPSIM")
    client.subscribe("DTSDA/LOADSIM")
    client.subscribe("DTSDA/END")
    client.subscribe("DTSDA/PLOTGRAF")
    #client.loop_start()
    print("------------------------> DTmqtt_messloop: loop forever")
    client.loop_forever()
    print("------------------------> DTmqtt_messloop: FINE metodo")
    
  
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
    

#taskRun()
#taskRunInThread1()


def SIMtest():
    #tRun = taskRunInThread2()
    taskRun()
    ## grafici attivati con il debug mode
    mosaik.util.plot_dataflow_graph(world, folder='util_figures')
    mosaik.util.plot_execution_graph(world, folder='util_figures')
    mosaik.util.plot_execution_time(world, folder='util_figures')
    mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
        

def on_message(client, userdata, message):
    # callback per messaggi MQTT
    global world, model, dtsdamng, tRun_on_message
    print(f'------------------------>on_message: Received con topic:{message.topic} message: {str(message.payload.decode("utf-8"))}')
    
    if message.topic == 'DTSDA/STOPSIM':
        print(f'------------------------>on_message:  FERMO LA SIMULAZIONE')
        world.until = 1
        sleep(1)
        print(f"SHUTDOWN!")       
        try:
            world.shutdown()
        except Exception as e:
            if debug:
                raise # re-raise the exception
                      # traceback gets printed
            else:
                print("{}: {}".format(type(e).__name__, e))

    elif  message.topic == 'DTSDA/RUNSIM':     
        print(f'------------------------>on_message:  RUN DELLA SIMULAZIONE')
        #------------------------------------------
        # Per sopprime il traceback!!!!
        sys.tracebacklimit = 0
        try:
            tRun_on_message = taskRunInThread2()
        except Exception as e:
            if debug:
                raise # re-raise the exception
                      # traceback gets printed
            else:
                print("{}: {}".format(type(e).__name__, e))


        sys.tracebacklimit = 1
        # FINE soppressione traceback!!!!
        #-----------------------------------------

    elif  message.topic == 'DTSDA/LOADSIM':     
        print(f'------------------------>on_message:  LOAD DELLA SIMULAZIONE')
        world, model, dtsdamng = prepScenario(SIM_CONFIG)

    elif  message.topic == 'DTSDA/SIM':     
        print(f'------------------------>on_message:  MODO SIMULAZIONE')
        pass

    elif  message.topic == 'DTSDA/LEARN':
        print(f'------------------------>on_message:  MODO LEARN')
        pass
        
    elif  message.topic == 'DTSDA/END':
        print(f'------------------------>on_message:  DISCONNET and END')
        client.disconnect()

    elif  message.topic == 'DTSDA/PLOTGRAF':
        print(f'------------------------>on_message:  PLOTGRAF per Debug')
        ## grafici attivati con il debug mode
        mosaik.util.plot_dataflow_graph(world, folder='util_figures')
        mosaik.util.plot_execution_graph(world, folder='util_figures')
        mosaik.util.plot_execution_time(world, folder='util_figures')
        mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
        
    else:
        pass


def main():
    global END
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    
    if args.test:
        print(f'Modalità TEST, {args.test}!')
        END=10
        SIMtest()
    else:
        DTmqtt_messloop()


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
world, model, dtsdamng = prepScenario(SIM_CONFIG)

#DTmqtt_messloop()  # messge loop mqtt
# END=10
# SIMtest()         # simulazione di test

if __name__ == '__main__':
    main()


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

# Esempio per accedere a variabili del simulatore:
# world.sims['ModelSim-0']._proxy.sim.entities['Model_0'].load_current
# world.sims['ModelSim-0'].output_to_push[('Model_0', 'DTmode_set')][0][1]  ritorna il valore di DTmode_set
# world.sims['ModelSim-0'].current_step.time         tempo corrente della task ModelSim-0

#------------------------------------------------------