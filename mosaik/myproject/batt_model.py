
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
import yaml
from pathlib import Path
#from .. src.digital_twin.bess import BatteryEnergyStorageSystem

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

#from src.digital_twin.bessMosaik import BatteryEnergyStorageSystem
from src.digital_twin.bess import BatteryEnergyStorageSystem

class Model:
    """

    """
    def __init__(self, **kwargs):
    #    super().__init__()
        models = ['thevenin', 'rc_thermal']
#    config_data_path = "./fmu_script/configuration"
#        config_data_path = "../scripts/fmi/fmu_script/configuration/"
        config_data_path = "mosaik/configuration/"
        experiment_config = "experiment_config.yaml"


        try:
            with open(Path(config_data_path) / Path(experiment_config), 'r') as fin:
                self.experiment_config = yaml.safe_load(fin)

        except Exception:
            raise FileExistsError("Selected configuration file doesn't exist.")


        """     
        pathf = config_data_path / Path(experiment_config)
        #pathf = "scripts/fmi/fmu_script/configuration/experiment_config.yaml"
        pathf = "mosaik/configuration/experiment_config.yaml"
        fin =   open(pathf, 'r')
        self.experiment_config = yaml.safe_load(fin)
        """    

        models_config_files = []
        for model in models:
            model_file = Path(self.experiment_config['models'][model]['category'] + '/' +
                              self.experiment_config['models'][model]['file'])
            models_config_files.append(config_data_path / model_file)

        self.battery = BatteryEnergyStorageSystem(
            models_config_files=models_config_files,
            battery_options=self.experiment_config['battery'],
            input_var=self.experiment_config['load']['var'],
#            output_var=self.experiment_config['ground']['var'],
#            units_checker=self.experiment_config['use_data_units'],
            sign_convention=self.experiment_config['sign_convention']         
        )

        self.battery.reset_data()
        self.battery.simulation_init(initial_conditions=self.experiment_config['initial_conditions'])

        self.load_current = 0.
        self.output_voltage = 0.
        #self.output_current = 0.
        self.k = 1
        self.sampling_time = self.experiment_config['time']['sampling_time']
        self.delta = 0.
        
    def step(self, sampling_time, current_time):
        """Perform a simulation step."""
        self.val = self.delta # valore dell'ingresso (input)
        #self.load_current = self.delta
        #self.output_current = self.load_current
        self.battery.simulation_step(load=self.val, dt=sampling_time, k=self.k)
#       self.output_voltage = self.battery.simulation_step(load=self.load_current, dt=sampling_time, k=self.k)
#       self.output_voltage = self.battery.results.pop('voltage')
        self.output_voltage = self.battery.results['voltage'][-1]
        self.load_current = self.battery.results['current'][-1]
        #= self.battery.results.pop('current')
        self.battery.t_series.append(current_time)
        self.k += 1
        return True

def test():
    model = Model()
    model.delta=12.45
    step =1.
    tcur=0.
    
    esito = model.step(step, tcur)
    print("esito=",esito,"load_current=",model.load_current,"output_voltage=",model.output_voltage)
    return(esito)


if __name__ == '__main__':
     test()



