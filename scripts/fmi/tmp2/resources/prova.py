from pythonfmu import Fmi2Causality, Fmi2Variability, Fmi2Slave, Real
import yaml
from pathlib import Path
import os




class Resistor(Fmi2Slave):

    author = "John Doe"
    description = "A simple description"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        models = ['thevenin', 'rc_thermal']
        config_data_path = "scripts/fmi/fmu_script/configuration"
        experiment_config = "experiment_config.yaml"
        cwd = os.getcwd()
        print("----->cwd=",cwd)
        with open(config_data_path / Path(experiment_config), 'r') as fin: self.experiment_config = yaml.safe_load(fin)
        

        self.positive_pin_v = 20.
        self.positive_pin_i = 0.001
        self.negative_pin_v = 10.
        self.negative_pin_i = 0.001
        self.delta_v = 10.
        self.i = 0.001
        self.R = 10000.
        
        self.register_variable(Real("R", causality=Fmi2Causality.parameter, variability=Fmi2Variability.tunable))

        self.register_variable(Real("positive_pin_v", causality=Fmi2Causality.input))
        self.register_variable(Real("positive_pin_i", causality=Fmi2Causality.output))
        self.register_variable(Real("negative_pin_v", causality=Fmi2Causality.input))
        self.register_variable(Real("negative_pin_i", causality=Fmi2Causality.output))

        self.register_variable(Real("delta_v", causality=Fmi2Causality.local))
        self.register_variable(Real("i", causality=Fmi2Causality.local))

    def do_step(self, current_time, step_size):
        self.delta_v = self.positive_pin_v - self.negative_pin_v
        self.i = i = self.delta_v / self.R
        self.positive_pin_i = i
        self.negative_pin_i = -i
        return True