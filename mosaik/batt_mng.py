"""
Mosaik interface for the example simulator.

It more complex than it needs to be to be more flexible and show off various
features of the mosaik API.

"""
from loguru import logger

import mosaik_api_v3
import redis
from  batt_include import *


META_DTSDAMng = {
    'type': 'event-based',
    'models': {'DTSDAMng': {'public': True,
                     'params': [],
                     'attrs': ['DTmode', 'DTmode_set'],
                     'trigger': ['DTmode_set'],                # input trigger per gli eventi
                     'non-persistent': ['DTmode'],     # output non-persistent per gli eventi

                     },
               }
}


class DTSDA_Mng(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(META_DTSDAMng)
        self.sid = None
        self.eid = None
        self.DTmode = None
        self.redis = None

    def init(self, sid, time_resolution):
        self.sid = sid

        #connessione a Redis, per il momento su localhost
        self.redis  = redis.Redis(host='localhost',port=6380)   
        if self.redis.exists('DTmode') != 0:
            self.DTmode = self.redis.get('DTmode').decode('utf-8') 
        else:
            self.DTmode = 'None'

        return self.meta

    def create(self, num, model):
        self.eid = 'DTSDAMng1'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        logger.info('step at {time} with inputs {inputs}', time=time, inputs=inputs)
        val = list(inputs[self.eid]['DTmode_set'].values())[0]
        if val != NOFORZ :
            self.DTmode = val
            self.redis.set('DTmode',val)
        else:
            self.DTmode = int(self.redis.get('DTmode'))

        return None

    def get_data(self, outputs):

        return {self.eid: {'DTmode': self.DTmode}}
    
    def finalize(self):
        self.redis.close()


def main():
    return mosaik_api_v3.start_simulation(DTSDA_Mng())

if __name__ == '__main__':
     main()