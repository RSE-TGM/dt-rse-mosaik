import mosaik
import mosaik_api_v3 as mosaik_api

#from mosaik.util import connect_randomly, connect_many_to_one
from mosaik.util import *
from batt_simulator import *
from batt_collector import *
from batt_mng import *
#import asyncio
#import mosaik.scheduler as scheduler

# Sim config. and other parameters
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
#world.connect(inpdata[0], monitor, 'LCU')
#world.connect(model, monitor, 'val', 'delta')
world.connect(model, monitor, 'load_current', 'output_voltage')
world.connect(model, influx, 'load_current', 'output_voltage')
#world.connect(model, monitor, 'output_voltage')

world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
#world.connect(model, dtsdamng, 'DTmode_set', weak=True)


#world.connect(dtsdamng, model, 'DTmode', weak=True)

#world.connect(dtsdamng, model, 'DTmode', time_shifted=True, initial_data={'DTmode': None})
world.connect(dtsdamng, model, 'DTmode')

world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')

#
# The method `World.connect()` takes one entity pair – the source and the destination entity, as well as a list of attributes or attribute tuples. 
# If you only provide single attribute names, mosaik assumes that the source and destination use the same attribute name. 
# If they differ, you can instead pass a tuple like `('val_out', 'val_in')`.
# 
# Quite often, you will neither create single entities nor connect single entity pairs, but work with large(r) sets of entities. 
# Mosaik allows you to easily create multiple entities with the same parameters at once. 
# It also provides some utility functions for connecting sets of entities with each other. 
# So lets create two more entities and connect them to our monitor:

# Create more entities
#more_models = examplesim.ExampleModel.create(2, init_val=3)
#####################   more_models = examplesim.ExampleModel.create(2)
#####################   mosaik.util.connect_many_to_one(world, more_models, monitor, 'val', 'delta')


# Instead of instantiating the example model directly, we called its static method `create()` and passed the number of instances to it. 
# It returns a list of entities (two in this case). 
# We used the utility function `mosaik.util.connect_many_to_one()` to connect all of them to the database. 
# This function has a similar signature as `World.connect()`, but the first two parameters are a world instance and a set (or list) of entities that are all connected to the dest_entity.
# 
# Mosaik also provides the function `mosaik.util.connect_randomly()`. This method randomly connects one set of entities to another set. These two methods should cover most use cases. 
# For more special ones, you can implement custom functions based on the primitive `World.connect()`.

#  The Simulation
# After we started, initialized, and connected the simulators, the scenario looks like shown in this figure:
# <div>
# <img src="scenario.png" width="600"/>
# </div>
# In order to start the simulation, we call `World.run()` and specify for how long we want our simulation to run and get the following output:


# Run simulation
#world.set_initial_event(dtsdamng.sid)

from threading import Thread
from time import sleep, perf_counter
import asyncio

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

async def do_stuff(i):
    ran = random.uniform(0.1, 0.5)
    await asyncio.sleep(ran)  # NOTE if we hadn't called
    # asyncio.set_event_loop() earlier, we would have to pass an event
    # loop to this function explicitly.
    print(i, ran)
    return ran


def thr(i):
    # we need to create a new loop for the thread, and set it as the 'default'
    # loop that will be returned by calls to asyncio.get_event_loop() from this
    # thread.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ret = loop.run_until_complete(do_stuff(i))
    loop.close()
    return ret

#taskRun()
#taskRunInThread1()
tRun = taskRunInThread2()

tRun.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
i=0
while tRun.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e vivo
    print(f"-----CHECK-TIMEOUT---Simulazione in RUN-{world.tqdm}------------------------------------------------------------------------------------------------------------>")
    tRun.join(timeout=1)  # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop
    if i > 3: 
        world.until = 1  # fermo (brutalmente) la simulazione
        #world.shutdown()
        print(f"Fermo tutto i={i}")
        
    i=i+1

sleep(3)
print(f"SHUTDOWN!")
world.shutdown()


## grafici attivati con il debug mode
# mosaik.util.plot_dataflow_graph(world, folder='util_figures')
# mosaik.util.plot_execution_graph(world, folder='util_figures')
# mosaik.util.plot_execution_time(world, folder='util_figures')
# mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')
#------------------------------------------------------

# # run di un'altra prova...
# world = mosaik.World(SIM_CONFIG, debug=True)   # debug true abilita i grafici dell'andamento della simulazione
# # Start simulators
# modelsim = world.start('ModelSim', eid_prefix='Model_')
# collector  = world.start('Collector')
# BATTplug = world.start('CSV', sim_start=START, datafile=INPUT_DATA)
# DTsdamng = world.start('DTSDA_Mng')
# # Instantiate models
# model   = modelsim.BattModel()
# monitor = collector.Monitor()
# LCUdata = BATTplug.Current.create(1)
# dtsdamng = DTsdamng.DTSDAMng()
# # Connect entities
# world.connect(LCUdata[0], model, ('LCU', 'load_current'))
# world.connect(model, monitor, 'load_current', 'output_voltage')
# world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
# world.connect(dtsdamng, model, 'DTmode')
# world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')
# world.run(until=END)