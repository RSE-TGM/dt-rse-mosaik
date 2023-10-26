# %% [markdown]
# ## Creating and running simple simulation scenarios
# We will now create a simple scenario with mosaik in which we use a simple data collector to print some output from our simulation. That means, we will instantiate a few ExampleModels and a data monitor. We will then connect the model instances to that monitor and simulate that for some time.

# %% [markdown]
# ## Configuration 
# You should define the most important configuration values for your simulation as “constants” on top of your scenario file. This makes it easier to see what’s going on and change the parameter values.
# 
# Two of the most important parameters that you need in almost every simulation are the simulator configuration and the duration of your simulation:

# %%
import mosaik
import mosaik.util
from batt_simulator import *
from batt_collector import *

#import import_ipynb

# Sim config. and other parameters
SIM_CONFIG = {
    'ExampleSim': {
        'python': 'batt_simulator:ExampleSim',
    },
    'Collector': {
        'python': 'batt_collector:Collector',
    },
}
END = 10  # 10 seconds

# %% [markdown]
# The sim config specifies which simulators are available and how to start them. In the example above, we list our ExampleSim as well as Collector (the names are arbitrarily chosen). For each simulator listed, we also specify how to start it.
# 
# Since our example simulator is, like mosaik, written in Python 3, mosaik can just import it and execute it in-process. The line `'python': '_02_simulator_mosaik:ExampleSim'` tells mosaik to import the package `_02_simulator_mosaik` and instantiate the class `ExampleSim` from it.
# 
# The [data collector](01_Integrate_Model/_03_collector.ipynb) will be started as external process which will communicate with mosaik via sockets. The line `'cmd': '%(python)s _03_collector.py %(addr)s'` tells mosaik to start the simulator by executing the command `python _03_collector.py.` Beforehand, mosaik replaces the placeholder `%(python)s` with the current python interpreter (the same as used to execute the scenario script) and `%(addr)s` with its actual socket address HOSTNAME:PORT so that the simulator knows where to connect to.

# %% [markdown]
# ## The world
# The next thing we do is instantiating a `World` object. This object will hold all simulation state. It knows which simulators are available and started, which entities exist and how they are connected. It also provides most of the functionality that you need for modelling your scenario:

# %%
# Create World
world = mosaik.World(SIM_CONFIG)

# %% [markdown]
# ## The Scenario
# Before we can instantiate any simulation models, we first need to start the respective simulators. This can be done by calling World.start(). It takes the name of the simulator to start and, optionally, some simulator parameters which will be passed to the simulators `init()` method. So lets start the example simulator and the data collector:

# %%
# Start simulators
examplesim = world.start('ExampleSim', eid_prefix='Model_')
collector  = world.start('Collector')

# %% [markdown]
# We also set the eid_prefix for our example simulator. What gets returned by `World.start()` is called a model factory.
# 
# We can use this factory object to create model instances within the respective simulator. 
# In your scenario, such an instance is represented as an `Entity`. 
# The model factory presents the available models as if they were classes within the factory’s namespace. 
# So this is how we can create one instance of our example model and one ‘Monitor’ instance:

# %%
# Instantiate models
#model = examplesim.ExampleModel(init_val=2)
model   = examplesim.ExampleModel()
monitor = collector.Monitor()

# %% [markdown]
# The init_val parameter that we passed to `ExampleModel` is the same as in the `create()` method of our Sim API implementation.
# 
# Now, we need to connect the example model to the monitor. That’s how we tell mosaik to send the outputs of the example model to the monitor.

# %%
# Connect entities
#world.connect(model, monitor, 'val', 'delta')
world.connect(model, monitor, 'load_current', 'output_voltage')

# %% [markdown]
# The method `World.connect()` takes one entity pair – the source and the destination entity, as well as a list of attributes or attribute tuples. If you only provide single attribute names, mosaik assumes that the source and destination use the same attribute name. If they differ, you can instead pass a tuple like `('val_out', 'val_in')`.
# 
# Quite often, you will neither create single entities nor connect single entity pairs, but work with large(r) sets of entities. Mosaik allows you to easily create multiple entities with the same parameters at once. It also provides some utility functions for connecting sets of entities with each other. So lets create two more entities and connect them to our monitor:

# %%
# Create more entities
#more_models = examplesim.ExampleModel.create(2, init_val=3)
#####################   more_models = examplesim.ExampleModel.create(2)
#####################   mosaik.util.connect_many_to_one(world, more_models, monitor, 'val', 'delta')

# %% [markdown]
# Instead of instantiating the example model directly, we called its static method `create()` and passed the number of instances to it. It returns a list of entities (two in this case). We used the utility function `mosaik.util.connect_many_to_one()` to connect all of them to the database. This function has a similar signature as `World.connect()`, but the first two parameters are a world instance and a set (or list) of entities that are all connected to the dest_entity.
# 
# Mosaik also provides the function `mosaik.util.connect_randomly()`. This method randomly connects one set of entities to another set. These two methods should cover most use cases. For more special ones, you can implement custom functions based on the primitive `World.connect()`.

# %% [markdown]
# ## The Simulation
# After we started, initialized, and connected the simulators, the scenario looks like shown in this figure:
# <div>
# <img src="scenario.png" width="600"/>
# </div>
# In order to start the simulation, we call `World.run()` and specify for how long we want our simulation to run and get the following output:

# %%
# Run simulation
world.run(until=END)

# %% [markdown]
# This was the first part of the mosaik tutorial.
# In the second part, a [control mechanism](../02_Integrate_Contoller/_01_controller.ipynb) is added to the scenario described here.


