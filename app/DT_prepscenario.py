""" inizializzazione del simulatore del DTwin """
#import sys
#import argparse
from time import sleep, perf_counter
# import logging as log
from loguru import logger

import mosaik
import datetime
import pytz
from pytz import timezone

from  DT_include import *

def DT_prepScenario():
    """ inizializzazione del simulatore del DTwin DTSDA In SIM_CONFIG sono definiti i componenti, le entity, di DTSDA 
    In seguito vine inizializzate le strutture dati di Mosaik, iniizializzate le entity il simulatore complessivo e definite le connessioni tra le entity
    """
    
    SIM_CONFIG = {
            'ModelSim': {
                'python': 'batt_model:ModelSim',
            },
            'Collector': {
                'python': 'DT_collector:Collector',
            },
            # 'CSV': {
            #     'python': 'mosaik_csv:CSV',
            # },
            'CSV': {
                'python': 'DT_mosaik_csv:CSV',
            },
            'DTSDA_Mng': {
                'python': 'batt_mng:DTSDA_Mng',
            },
# componente di mosaik ...
#            'InfluxWriter': {
#                'python': 'mosaik.components.influxdb2.writer:Simulator',
#
# ho scaricato il componente ed uso direttamente quello per una migliore gestione e debug
            'InfluxWriter': {
                'python': 'influxdb2_writer:Simulator',
            },
        }

    # Create World
    #world = mosaik.World(SIM_CONFIG, time_resolution=0.5)
    world = mosaik.World(SIM_CONFIG, debug=True)   # debug true abilita i grafici dell'andamento della simulazione

    
    #START = '2023-01-01 01:00:00'
    now = datetime.datetime.now(pytz.timezone(TZONE))
    START = f"{now}"
    ### INPUT_DATA = 'mosaik/configuration/data/input_data.csv' # .csv in your setup
    INPUT_DATA = CONFIG_DATA_PATH + CURR_CONFIG['DT_input_data']
    #INPUT_DATA = 'configuration/data/input_data.csv' # .csv in your setup

    # Start simulators
    #modelsim = world.start('ModelSim', eid_prefix='Model_',step_size=2.8)
    modelsim = world.start('ModelSim', eid_prefix='Model_')
    collector  = world.start('Collector', step_size=1, start_date=START,saveHistory=False)

    STARTDATAFILE= '2023-01-01 01:00:00'
    BATTplug = world.start('CSV', sim_start=STARTDATAFILE, datafile=INPUT_DATA, replay=True)    # replay=True ripete periodicamente la perturbazione

    DTsdamng= world.start('DTSDA_Mng')

    #INIZTIME= '2024-01-13 17:00:00'
    influx_sim = world.start('InfluxWriter', step_size=1, start_date=START, printDebug=False)

    # Instantiate models
    #model = examplesim.ExampleModel(init_val=2)
    model   = modelsim.BattModel()
    monitor = collector.Monitor()
    LCUdata = BATTplug.Current.create(1)
    dtsdamng = DTsdamng.DTSDAMng()
    

    # Connessione a influxdb server e get instance
    infl_inst = InfluxDBCli(influx_sim)   # i parametri di connessione sono nel file config yaml
    influx = infl_inst.getinflux()
    # influx = influx_sim.Database(
    #     url="http://localhost:8086",
    #     org='RSE',
    #     bucket='nuovobuck',
    #     token='aHMudy-R1gicVNWRDzVTWmw4_HPFVCdwzcUTIErKl_i2uVRpCrCpmTOtcOAg0n-qNdnuetSQfTKGHAmgsMeL4A==',
    #     measurement='experiment_0001'
    # )



    # Connect entities
    world.connect(LCUdata[0], model, ('LCU', 'load_current'))  # 1 output di LCUdata ('LCU'), connesso con 1 imput di model ('load_curremt')
    world.connect(model, monitor, 'load_current', 'output_voltage','soc','soh','Vocv','power','temperature','heat','C','R0','R1')  # 11 outputs di model ('load_current' e 'output_voltage') connessi  a  2 inputs di monitor con lo stesso nome
    world.connect(model, influx, 'load_current', 'output_voltage','soc','soh','Vocv','power','temperature','heat','C','R0','R1')
    world.connect(model, dtsdamng, 'DTmode_set', time_shifted=True, initial_data={'DTmode_set': NOFORZ})
    world.connect(dtsdamng, model, 'DTmode')
    world.connect(dtsdamng, monitor, 'DTmode', 'DTmode_set')
    return (world, model, dtsdamng)



if __name__ == '__main__':
    debug=True
    DT_prepScenario()
