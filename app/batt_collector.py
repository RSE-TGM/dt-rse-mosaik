
# ## Data Collector
# Here is the complete file of the data collector:

"""
A simple data collector that prints all data when the simulation finishes.

"""
import collections

import mosaik_api_v3 as mosaik_api

from  DT_include import *


META_Monitor = {
    'type': 'event-based',
    'models': {
        'Monitor': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
        },
    },
}


class Collector(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META_Monitor)
        self.eid = None
        self.data = collections.defaultdict(lambda:
                                            collections.defaultdict(dict))
        
        self.redis = redisDT()     # legge il file di configurazione e crea oggetto redis  
        self.tags = self.redis.gettags()
        self.r = self.redis.connect()
  

    def init(self, sid, time_resolution):
        return self.meta

    def create(self, num, model):
        if num > 1 or self.eid is not None:
            raise RuntimeError('Can only create one instance of Monitor.')

        self.eid = 'Monitor'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        data = inputs.get(self.eid, {})
        self.redis.aset('tsim',str(time), hmode=True)
        for attr, values in data.items():
            for src, value in values.items():
                self.data[src][attr][time] = value
                #savetoredis(src,attr,time,value)
                if attr != 'DTmode' and attr != 'DTmode_set' : self.redis.aset(attr,str(value), hmode=True)

        return None
    
    def finalize(self):
        print('Collected data:')
        for sim, sim_data in sorted(self.data.items()):
            print('- %s:' % sim)
            for attr, values in sorted(sim_data.items()):
                print('  - %s: %s' % (attr, values))

if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
