
#import sys
#import argparse
from time import sleep, perf_counter
# import logging as log
from loguru import logger

import mosaik
import datetime

from  DT_include import *

def batt_prepScenario():

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

    # Create World
    #world = mosaik.World(SIM_CONFIG, time_resolution=0.5)
    world = mosaik.World(SIM_CONFIG, debug=True)   # debug true abilita i grafici dell'andamento della simulazione

    
    #START = '2023-01-01 01:00:00'
    now = datetime.datetime.now()
    START = f"{now}"
    ### INPUT_DATA = 'mosaik/configuration/data/input_data.csv' # .csv in your setup
    INPUT_DATA = 'configuration/data/input_data.csv' # .csv in your setup

    # Start simulators
    #modelsim = world.start('ModelSim', eid_prefix='Model_',step_size=2.8)
    modelsim = world.start('ModelSim', eid_prefix='Model_')
    collector  = world.start('Collector')

    STARTDATAFILE= '2023-01-01 01:00:00'
    BATTplug = world.start('CSV', sim_start=STARTDATAFILE, datafile=INPUT_DATA)

    DTsdamng= world.start('DTSDA_Mng')

    #INIZTIME= '2024-01-13 17:00:00'
    INIZTIME= START
    influx_sim = world.start('InfluxWriter', step_size=1, start_date=INIZTIME)

    # Instantiate models
    #model = examplesim.ExampleModel(init_val=2)
    model   = modelsim.BattModel()
    monitor = collector.Monitor()
    LCUdata = BATTplug.Current.create(1)
    dtsdamng = DTsdamng.DTSDAMng()
    

    # Connessione a influxdb server e get instance
    infl_inst = InfluxDBCli(influx_sim)
    influx = infl_inst.getinflux()
    # influx = influx_sim.Database(
    #     url="http://localhost:8086",
    #     org='RSE',
    #     bucket='nuovobuck',
    #     token='aHMudy-R1gicVNWRDzVTWmw4_HPFVCdwzcUTIErKl_i2uVRpCrCpmTOtcOAg0n-qNdnuetSQfTKGHAmgsMeL4A==',
    #     measurement='experiment_0001'
    # )



    # Connect entities
    world.connect(LCUdata[0], model, ('LCU', 'load_current'))
    world.connect(model, monitor, 'load_current', 'output_voltage')
    world.connect(model, influx, 'load_current', 'output_voltage')
    world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
    world.connect(dtsdamng, model, 'DTmode')
    world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')
    return (world, model, dtsdamng)



if __name__ == '__main__':
    debug=True
    batt_prepScenario()