"""
Mosaik interface for the example simulator.

"""
import os, sys;
#import import_ipynb
from loguru import logger
import mosaik_api_v3 as mosaik_api
# import batt_model
from  DT_include import *

from pathlib import Path
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

from src.digital_twin.orchestrator.base_manager import GeneralPurposeManager

META_Battmodel = {
#    'type': 'time-based',
    'type': 'hybrid',
    'models': {
        'BattModel': {
            'public': True,
            'params': ['init_val'],
            'attrs': ['load_current', 
                      'output_voltage',
                      'DTmode_set',
                      'DTmode'],
            'trigger': ['DTmode'],                # input: trigger per gli eventi
            'non-persistent': ['DTmode_set'],     # output: non-persistent per gli eventi
        },
    },
}


class ModelSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META_Battmodel)
        self.eid_prefix = 'Model_'
        self.entities = {}  # Maps EIDs to model instances/entities
        self.time = 0

    def init(self, sid, time_resolution, eid_prefix=None):     # init(self, sid, time_resolution, eid_prefix=None, step_size=1):

        args={  'config_folder': './data/config', 
            'output_folder': './data/output', 
            'ground_folder': './data/ground', 
            'assets': './data/config/assets.yaml', 
            'battery_model': ['thevenin'], 
            'thermal_model': ['mlp_thermal'], 
            'aging_model': None, 
            'save_results': False, 
            'save_metrics': False, 
            'plot': False, 
            'n_cores': 1, 
            'verbose': True, 
            'mode': 'simulation', 
            'config_files': ['./data/config/sim_config_example.yaml']
            }

        # Parsing of models employed in the current experiment
        args['models'] = []
        if args['battery_model']:
            args['models'].extend(args['battery_model'])
            del args['battery_model']

        if args['thermal_model']:
            args['models'].extend(args['thermal_model'])
            del args['thermal_model']

        if args['aging_model']:
            args['models'].extend(args['aging_model'])
            del args['aging_model']

        self.config_file = args['config_files']
        del args['config_files']

        n_cores = args['n_cores']
        del args['n_cores']
        
        self.args=args

        if float(time_resolution) != 1.:
            raise ValueError('ModelSim only supports time_resolution=1., but'
                             ' %s was set.' % time_resolution)
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        
        return self.meta

    def create(self, num, model):
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
#            model_instance = batt_model.Model(init_val)

#            model_instance = batt_model.Model()

            model_instanceGen = GeneralPurposeManager.get_instance(self.args['mode'])
            self.args['config'] = self.config_file[0]        
            model_instance= model_instanceGen(**self.args)

            model_instance.DTmode_set = NOFORZ  # é un'uscita per un eventuale forzamento di DTmode
            model_instance.DTmode = None
            eid = '%s%d' % (self.eid_prefix, i)
            self.entities[eid] = model_instance
            entities.append({'eid': eid, 'type': model})

        return entities


    def step(self, time, inputs, max_advance):           
        self.time = time

       # Check for new delta and do step for each model instance:
        for eid, model_instance in self.entities.items():
            if eid in inputs:
                attrs = inputs[eid]
                for attr, values in attrs.items():
                    if attr == 'DTmode':
                        model_instance.DTmode = list(values.values())[0]
                    if attr == 'load_current':
                        #model_instance.load_current = list(values.values())[0] #  era sum(values.values()), corrente allo step successivo
                        model_instance._input_var='current'
                        model_instance._ground_data[model_instance._input_var][0]=list(values.values())[0]
            
            sampling_time=model_instance._stepsize   # model_instance.sampling_time è letto dal file di config experiment
            
            if model_instance.DTmode == MODSIM :
                model_instance.run_step()   # sono in modo "simulazione"
                modo=S_SIM
            else:
                model_instance.learn(sampling_time, time)  # sono in modo "learn"
                modo=S_LEARN
               
        
        next_step = time + int(sampling_time) 
        model_instance.load_current=9
        model_instance.output_voltage=99
        model_instance.delta=999
        logger.info('batt_model: time={time} sampling_time={sampling_time} - La batteria è in modalità {modo}, current[A]={current} voltage[V]={voltage} next_current[A]={next_step_current}', time=time, sampling_time=sampling_time, modo=modo, 
                    current=model_instance.load_current, voltage=model_instance.output_voltage, next_step_current=model_instance.delta)
        print(f'------>  {model_instance._results}')
        return next_step  # Step size, cioè sampling_time, è normalmmente 1 secondo ed è letto dal file di config experiment

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            model = self.entities[eid]
            data['time'] = self.time
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['BattModel']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)

                # Get model.val or model.delta:
                data[eid][attr] = getattr(model, attr)

        return data


def main():
    return mosaik_api.start_simulation(ModelSim())


if __name__ == '__main__':
     main()



