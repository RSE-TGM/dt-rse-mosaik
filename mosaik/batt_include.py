
# DTSDA
# definizioni di variabili e funzioni varie

import yaml
from pathlib import Path


MODSIM = 'SIM'    # era 1
MODLEARN = 'LRN'  # era 10
NOFORZ = '0'      # era 0
FORZSIM = MODSIM
FORZLEARN = MODLEARN
STOP = -1

def readConfig(config_path, namefile):
        # Read in memory a yalm file
        
        #config_path = "mosaik/configuration/"
        #namefile = "experiment_config.yaml"
        try:
            with open(Path(config_path) / Path(namefile), 'r') as fin:
                return yaml.safe_load(fin)
        except Exception:
            raise FileExistsError("Selected configuration file doesn't exist.")
            return None 


        
