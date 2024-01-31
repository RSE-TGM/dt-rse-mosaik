"""
Mosaik interface for the example simulator.

It more complex than it needs to be to be more flexible and show off various
features of the mosaik API.

"""
from loguru import logger
import os
import mosaik_api_v3
import redis
from  batt_include import *


META_DTSDAMng = {
    'type': 'hybrid',
#    'type': 'event-based',
    'models': {'DTSDAMng': {'public': True,
                     'params': [],
                     'attrs': ['DTmode_set','DTmode'],
                     'trigger': ['DTmode_set'],                # input - trigger per gli eventi
                     'non-persistent': ['DTmode'],     # output - non-persistent per gli eventi

                     },
               }
}


class DTSDA_Mng(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(META_DTSDAMng)
        self.sid = None
        self.eid = None
        self.DTmode = None
        self.DTmode_set = None
        self.redis = None

    def init(self, sid, time_resolution):
        self.sid = sid

        #connessione a Redis, per il momento su localhost

        config_data_path = "mosaik/configuration/"
        self.configDT = "configDT.yaml"

        self.configDT = readConfig(config_data_path, self.configDT)

        redis_host = os.getenv(self.configDT['redis']['redis_host'])
        if redis_host == None:
            redis_host = self.configDT['redis']['redis_host_default']

        redis_port = os.getenv(self.configDT['redis']['redis_port'])
        if redis_port == None:
            redis_port = self.configDT['redis']['redis_port_default']
        

        #self.redis = redis.Redis(host=redis_host, port=redis_port, charset="utf-8", decode_responses=True)

        self.redis  = redis.Redis(host=redis_host,port=redis_port)   
        try:
            response = self.redis.client_list()
        except redis.ConnectionError:
            logger.info("REDIS: NON esiste  il servizio: {redis_host} {redis_port}!!",redis_host=redis_host,redis_port=redis_port )
            exit(1)

        if self.redis.exists('DT:mode') != 0:
#            self.DTmode = self.redis.get('DTmode')
            self.DTmode = self.redis.get('DT:mode').decode('utf-8') 
        else:
            self.DTmode = self.configDT['redis']['DT:mode'] # se non esiste metto il dafault letto dal configDT
            self.redis.set('DT:mode',self.DTmode)

        if self.redis.exists('DT:mode_set') != 0:
#            self.DTmode = self.redis.get('DTmode')
            self.DTmode_set = self.redis.get('DT:mode_set').decode('utf-8') 
        else:
            self.DTmode_set = self.configDT['redis']['DT:mode_set'] # se non esiste metto il dafault letto dal configDT
            self.redis.set('DT:mode_set',self.DTmode_set)

        logger.info('REDIS:  redis_host={redis_host} redis_port={redis_port}', redis_host=redis_host, redis_port=redis_port)


        return self.meta

    def create(self, num, model):
        self.eid = 'DTSDAMng'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        val = list(inputs[self.eid]['DTmode_set'].values())[0]
        logger.info('step at {time} with inputs {inputs}, DTmode_set={DTmode_set}', time=time, inputs=inputs,DTmode_set=val)

        # match val:
        #     case NOFORZ:
        #         self.DTmode = int(self.redis.get('DT:mode'))                
        #     case FORZSIM:
        #         self.redis.set('DT:mode',self.redis.set('DT:mode',val))
        #     case _:
        # val = NOFORZ
        if val == NOFORZ :
            self.DTmode = self.redis.get('DT:mode').decode('utf-8')   # int(self.redis.get('DT:mode'))
        elif val == FORZSIM:
            self.DTmode = val
            self.redis.set('DT:mode',val)
        elif val == FORZLEARN:
            self.DTmode = val
            self.redis.set('DT:mode',val)
        
        
        # if (int(self.redis.get('DT:mode_set')) == STOP) :
        #     logger.info('!!! STOP  !! step at {time} with inputs {inputs}', time=time, inputs=inputs)
        #     return 1000000000

        #return time + 1   # se è hybrid
        return None     # se è event-base

    def get_data(self, outputs):
        logger.info('get_data with {outputs}, self.DTmode {DTmode}', outputs=outputs, DTmode=self.DTmode)
        return {self.eid: {'DTmode': self.DTmode}}
    
    def finalize(self):
        self.redis.close()


def main():
    return mosaik_api_v3.start_simulation(DTSDA_Mng())

if __name__ == '__main__':
     main()