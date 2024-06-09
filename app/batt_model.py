
"""
batt_model.py
This module contains the battery model for mosaik.

"""

""" try:
    import os
    import numpy as np
    import yaml
    from pathlib import Path
    from ..src.digital_twin.bess import BatteryEnergyStorageSystem

except ImportError:
    os, np, yaml, Path, BatteryEnergyStorageSystem = None, None, None, None, None
    print(os, np, yaml, Path, BatteryEnergyStorageSystem) """



import os, sys; 
import numpy as np
#import yaml
from loguru import logger
from pathlib import Path
#from .. src.digital_twin.bess import BatteryEnergyStorageSystem

from  DT_include import readConfig

from  DT_include import CONFIG_DATA_PATH
from  DT_include import EXPERIMENT_CONFIG
from  DT_include import  SRC_DTRSE

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# aggiunge nel path la directory base del package, ad esempio: /home/antonio/dtwin/dt-rse-mosaik
### sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))  

# sys.path.append(os.path.dirname(SCRIPT_DIR)) # per src locale 

#######################################################################
if SRC_DTRSE:
    SRC_DT_RSE=  os.path.dirname(SCRIPT_DIR)+'/DT-rse'
    sys.path.append(SRC_DT_RSE)                  # per src di DT-rse
else:
    sys.path.append(os.path.dirname(SCRIPT_DIR)) # per src locale
#######################################################################

# a questo punto riesco a trovare src.digital_twin.bess
from src.digital_twin.bess import BatteryEnergyStorageSystem



class Model:
    """

    """
    def __init__(self, **kwargs):
        super().__init__()
        models = ['thevenin', 'rc_thermal']


#        config_data_path = "mosaik/configuration/"
#        experiment_config = "experiment_config.yaml"
        config_data_path = CONFIG_DATA_PATH
        experiment_config = EXPERIMENT_CONFIG

        self.experiment_config = readConfig(config_data_path, experiment_config)


        # try:
        #     with open(Path(config_data_path) / Path(experiment_config), 'r') as fin:
        #         self.experiment_config = yaml.safe_load(fin)
        # except Exception:
        #     raise FileExistsError("Selected configuration file doesn't exist.")


        # pathf = config_data_path / Path(experiment_config)
        # #pathf = "scripts/fmi/fmu_script/configuration/experiment_config.yaml"
        # pathf = "mosaik/configuration/experiment_config.yaml"
        # fin =   open(pathf, 'r')
        # self.experiment_config = yaml.safe_load(fin)
    

        models_config_files = []
        for model in models:
            model_file = Path(self.experiment_config['models'][model]['category'] + '/' +
                              self.experiment_config['models'][model]['file'])
            models_config_files.append(config_data_path / model_file)

        self.battery = BatteryEnergyStorageSystem(
            models_config_files=models_config_files,
            battery_options=self.experiment_config['battery'],
            input_var=self.experiment_config['load']['var'],
            sign_convention=self.experiment_config['sign_convention']         
        )

        self.battery.reset_data()
        self.battery.simulation_init(initial_conditions=self.experiment_config['initial_conditions'])

        self.load_current = 0.
        self.output_voltage = 0.
        
        self.k = 1
        self.sampling_time = self.experiment_config['time']['sampling_time']
        self.delta = 0.
        
    def step(self, sampling_time, current_time):
        """Perform a simulation step."""
        #  self.delta valore dell'ingresso (input). Eseguo uno step di calcolo ...
        self.battery.simulation_step(load=self.delta, dt=sampling_time, k=self.k)
        # carico i risultati dello step di calcolo 
        self.output_voltage = self.battery.results['voltage'][-1]
        self.load_current = self.battery.results['current'][-1]
        self.battery.t_series.append(current_time)
        self.k += 1
        return True
    def learn(self, sampling_time, current_time):
        logger.info('batt_model: La batteria è in modalità LEARN, self.DTmode {DTmode}', DTmode=self.DTmode)
        pass

def test():
    model = Model()
    model.delta=12.45  # current (A)
    step =1.  # incremento in secondi
    tcur=0.   
    for tcur in range(0,10,1):
        model.delta=model.delta+0.1
        esito = model.step(step, tcur)
        print("esito=",esito,"T=",tcur, "sec.", "- load_current=",model.load_current,"output_voltage=",model.output_voltage)
    
    return(esito)


if __name__ == '__main__':
     test()



