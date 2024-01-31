import mosaik
import mosaik_api_v3 as mosaik_api

#from mosaik.util import connect_randomly, connect_many_to_one
from mosaik.util import *
from batt_simulator import *
from batt_collector import *
from batt_mng import *
import asyncio
#import mosaik.scheduler as scheduler


# import nest_asyncio

# # 👇️ call apply()
# nest_asyncio.apply()



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

END = 2099  # 10 seconds
#END = 1 * 24 * 60 * 60 # one day in seconds

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

#world.run(until=END)
#world.run(until=END,rt_factor=1.1)
#### asyncio.run(world.run(until=END,rt_factor=1.1))


# def work(world):
#     print('Task starting')
#     world.run(until=END,rt_factor=1.1)
#     #asyncio.run(world.run(until=END,rt_factor=1.1))
#     print('Task done')
    
# async def main(world):
#     print("IN main .....")
#     coro = asyncio.to_thread(work(world))
#     print('dopo thread')
#     # await asyncio.sleep(1)
# ##    asyncio.sleep(1)
#     print('dopo thread e asyncio.sleep')  
# # schedule the task
# ###    task = asyncio.create_task(coro)
# # suspend a moment, allow the new thread to start
#     await asyncio.sleep(1)
#     print('Main done')
    


# async def my_coroutine(world):
#     print('Task starting')
#     world.run(until=END,rt_factor=1.1)
#     print("Running my_coroutine")


# async def main(world):
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(my_coroutine(world))
#     # print("prima di my_coroutine")
#     # asyncio.run(my_coroutine(world))
#     # print("DOPO my_coroutine")
#     print("FINE mainS")
    

# #### prove con threading
# import threading

# from datetime import datetime
# now = datetime.now


# #async def test_timer_function(world):
# def test_timer_function(world):
#     #await asyncio.sleep(2)
#     world.run(until=END,rt_factor=1.1)
#     print(f"ending async task at {now()}")
#     return

# def run_async_loop_in_thread(world):
#     asyncio.run(test_timer_function(world))

# def main(world):
#     print(f"Starting timer at {now()}")
# #    t = threading.Thread(target=run_async_loop_in_thread(world))
#     t = threading.Thread(target=test_timer_function(world))
# #    t = threading.Thread(target=world.run(until=END,rt_factor=1.1))
#     print("DOPO Thread")
# #    t.start()
#     print(f"Ending timer at {now()}")
#     return t

# if __name__ == "__main__":
#     t = main()
#     t.join()
#     print(f"asyncio thread exited normally at {now()}")

#print("PRIMA main world.run -------------------------------------------------------------------------------")
#t = main(world)
#t.join()
#print(f"asyncio thread exited normally at {now()}")






#asyncio.run(main(world))
#main(world)


#print("DOPO main world.run ----------------------------------------------------------------------------FINE----")


from time import sleep, perf_counter
from datetime import datetime
now = datetime.now
from threading import Thread


def task1():
    print(f'Starting a task at {now()}')
    sleep(1)
    print(f'Done the task at {now()}')

def task2():
    print(f'Starting a task at {now()}')
    world.run(until=END,rt_factor=1.1)
    print(f'Done the task at {now()}')



start_time = perf_counter()
print(f'prima di target={start_time}')
# create two new threads
t1 = Thread(target=task1)
t2 = Thread(target=task2)
print(f'dopo di target={now()}')
sleep(1)
# start the threads
print(f"prima di start={now()}")
t1.start()
t2.start()
sleep(1)
#world.until=10
print(f"dopo di start={now()}")

# wait for the threads to complete
t1.join()
t2.join(timeout=1) # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop 
i=0
while t2.is_alive():   # se il thread è vivo, vuol dire che ho aspettato un secondo e non ha finito perchè e vivo
    t2.join(timeout=1)  # mi aggancio al thread ed aspetto max 1 secondo, se ha finito esco, se non ha finito allora vado in loop
    print(f"-----TIMEOUT---------------------------------------------------------------------------------------------------------------------------------------->")
    if i > 3: 
        world.until = 1  # fermo (brutalmente) la simulazione
        print(f"Fermo tutto i={i}")
    i=i+1

pass  # il tread ha finito

#t2.join()

end_time = perf_counter()

print(f'It took {end_time - start_time: 0.2f} second(s) to complete.')

## asyncio.run(scheduler.run(world,until=END,rt_factor=1.))

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