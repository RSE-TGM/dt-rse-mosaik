import os
import mosaik
import mosaik_api_v3 as mosaik_api
from mosaik_fmi.mosaik_fmi import FmuAdapter
from mosaik.util import connect_randomly, connect_many_to_one

from app.batt_model import *
from app.DT_collector import *

# Lo start di questo script deve essere eseguito nella home del package:  dt-rse-mosaik/

# Sim config. and other parameters
SIM_CONFIG = {
    'ModelSimFmu': {
        'python': 'mosaik_fmi.mosaik_fmi:FmuAdapter',    # mosaik_fmi è un component di mosaik, usa la fmu DTMockup.fmu
    },
    'ModelSim': {
       'python': 'batt_simulator:ModelSim',
    },
    'Collector': {
        'python': 'batt_collector:Collector',
    },
        'CSV': {
        'python': 'mosaik_csv:CSV'                        # mosaik_csv è un component di mosaik, legge il file data/input_data.csv con un profilo di corrente del carico
    },

}
END = 10  # imposto 10 secondi di simulazione
#END = 1 * 24 * 60 * 60 # one day in seconds

# Create World
world = mosaik.World(SIM_CONFIG, debug=True)

# Add PV data file
START = '2023-01-01 01:00:00'
INPUT_DATA = 'mosaik/configuration/data/input_data.csv' # .csv in your setup


# Start simulators
fmupath_rel ='./scripts/fmi/fmu'
fmupath_abs = os.path.realpath(fmupath_rel)  # path assoluto della fmu
modelsimFmu = world.start('ModelSimFmu',
                    work_dir=fmupath_abs,
                    fmu_name='DTMockup',     # è la DTMockup.fmu
                    fmi_version='2',
                    fmi_type='cs',
                    logging_on=False,
                    instance_name='DTMockup',
                    step_size=1
)
modelsim  = world.start('ModelSim', eid_prefix='Model_,b')
collector = world.start('Collector')
BATTplug  = world.start('CSV', sim_start=START, datafile=INPUT_DATA)


# Instantiate models
modelFmu = modelsimFmu.DTMockup.create(1,load_current=2107.0)
model    = modelsim.BattModel()
monitor  = collector.Monitor()
LCUdata  = BATTplug.Current.create(1)

# Connect entities
world.connect(LCUdata[0], model, ('LCU', 'load_current')) # se hanno lo stesso nome:  world.connect(LCUdata[0], model, 'nome_var')
world.connect(LCUdata[0], modelFmu[0], ('LCU', 'load_current'))

#world.connect(inpdata[0], monitor, 'LCU')
#world.connect(model, monitor, 'val', 'delta')


world.connect(model, monitor, 'load_current', 'output_voltage')
world.connect(modelFmu[0], monitor,'output_voltage')
#
# The method `World.connect()` takes one entity pair – the source and the destination entity, as well as a list of attributes or attribute tuples. If you only provide single attribute names, mosaik assumes that the source and destination use the same attribute name. If they differ, you can instead pass a tuple like `('val_out', 'val_in')`.
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

#----------------------
# Run simulation
world.run(until=END)
#----------------------
mosaik.util.plot_dataflow_graph(world, folder='util_figures')
mosaik.util.plot_execution_graph(world, folder='util_figures')
mosaik.util.plot_execution_time(world, folder='util_figures')
mosaik.util.plot_execution_time_per_simulator(world, folder='util_figures')


