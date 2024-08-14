
# ## Data Collector
# Here is the complete file of the data collector:

"""
Semplice data collector che salva e stampa tutte le variabili alla fine della simulazione e scrive su una hash table di redis.
La scrittura su redis viene sempre eseguita ad ogni passo, mentre il salvataggio e la stampa finale è condizionata dalla variabile saveHistory.

"""
import collections

import mosaik_api_v3 as mosaik_api
from mosaik_api.datetime import Converter

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
  

    def init(self, sid, time_resolution,  start_date=None, step_size=1, saveHistory=True):
        self.saveHistory=saveHistory
        if start_date:
            self._time_converter = Converter(
                start_date=start_date,
                time_resolution=time_resolution,
            )
        return self.meta

    def create(self, num, model):
        if num > 1 or self.eid is not None:
            raise RuntimeError('Can only create one instance of Monitor.')

        self.eid = 'Monitor'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):       
        data = inputs.get(self.eid, {})

        if "local_time" in data:
            timestamp = next(iter(data["local_time"].values()))
            print(f"collector: timestamp={timestamp} ")
        elif self._time_converter:
            timestamp = self._time_converter.isoformat_from_step(time)

        self.redis.aset('tsim',str(time), hmode=True)
        self.redis.aset('timestamp',str(timestamp), hmode=True)
        
        for attr, values in data.items():
            for src, value in values.items():
                if self.saveHistory: self.data[src][attr][time] = value
                #savetoredis(src,attr,time,value)                
                if attr != 'DTmode' and attr != 'DTmode_set' : 
                    valueApross='%.3f' % round(value * 1000 / 1000,3)  # 3 decimali
                    self.redis.aset(attr,str(valueApross), hmode=True)

        return None
    
    def finalize(self):
        if self.saveHistory: 
            print('Collected data:')
            for sim, sim_data in sorted(self.data.items()):
                print('- %s:' % sim)
                for attr, values in sorted(sim_data.items()):
                    print('  - %s: %s' % (attr, values))

if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
