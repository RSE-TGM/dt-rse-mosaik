import mosaik
import mosaik_api_v3 as mosaik_api
from mosaik.util import *
from batt_simulator import *
from batt_collector import *
from batt_mng import *
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
END = 100  # 100 seconds
# Create World
world = mosaik.World(SIM_CONFIG, debug=True)   # debug true abilita i grafici dell'andamento della simulazione
now = datetime.datetime.now()
START = f"{now}"
INPUT_DATA = 'mosaik/configuration/data/input_data.csv' # .csv in your setup

# Start simulators
modelsim = world.start('ModelSim', eid_prefix='Model_')
collector  = world.start('Collector')
STARTDATAFILE= '2023-01-01 01:00:00'
BATTplug = world.start('CSV', sim_start=STARTDATAFILE, datafile=INPUT_DATA)
DTsdamng= world.start('DTSDA_Mng')
INIZTIME= START
influx_sim = world.start('InfluxWriter', step_size=1,   start_date=INIZTIME)

# Instantiate models
model   = modelsim.BattModel()
monitor = collector.Monitor()
LCUdata = BATTplug.Current.create(1)
dtsdamng = DTsdamng.DTSDAMng()
influx = influx_sim.Database(
    url="http://localhost:8086",
    org='RSE',
    bucket='nuovobuck',
    token='aHMudy-R1gicVNWRDzVTWmw4_HPFVCdwzcUTIErKl_i2uVRpCrCpmTOtcOAg0n-qNdnuetSQfTKGHAmgsMeL4A==',
    measurement='experiment_0001')

# Connect entities
world.connect(LCUdata[0], model, ('LCU', 'load_current'))
world.connect(model, monitor, 'load_current', 'output_voltage')
world.connect(model, influx, 'load_current', 'output_voltage')
world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
world.connect(dtsdamng, model, 'DTmode')
world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')

# Run simulation
world.run(until=END,rt_factor=1.1)