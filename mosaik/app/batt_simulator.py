"""
Mosaik interface for the example simulator.

"""

#import import_ipynb
from loguru import logger
import mosaik_api_v3 as mosaik_api
import batt_model
from  DT_include import *

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
            model_instance = batt_model.Model()
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
                        model_instance.delta = list(values.values())[0] #  era sum(values.values())
            
            sampling_time=model_instance.sampling_time   # model_instance.sampling_time è letto dal file di config experiment
            
            if model_instance.DTmode == MODSIM :
                model_instance.step(sampling_time, time)   # sono in modo "simulazione"
            else:
                model_instance.learn(sampling_time, time)  # sono in modo "learn"
               
        
        
        # if time >= 5 :
        #     extra = 10000000
        # else:
        #     extra = 0
        # 
        # next_step = time + sampling_time + extra
        
        next_step = time + sampling_time 
        logger.info('batt_model: {time} La batteria è in modalità self.DTmode {DTmode}, nextstep ={next_step}', time=time, DTmode=model_instance.DTmode, next_step=next_step)
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



