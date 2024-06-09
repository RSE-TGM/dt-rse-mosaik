"""
Mosaik interface for the example simulator.

It more complex than it needs to be to be more flexible and show off various
features of the mosaik API.

"""
from loguru import logger
import os
import mosaik_api_v3
import redis
from  DT_include import *


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

        #connessione a Redis, in fase di test su localhost
        self.redis = redisDT()     # legge il file di configurazione e crea oggetto redis  
        self.tags = self.redis.gettags()
        self.r = self.redis.connect()
        

        if self.redis.esistetag(self.tags['DTmode'][0]) != 0:
            self.DTmode = self.tags['DTmode'][0]
        else:
            self.DTmode = self.tags['DTmode'][1] # se non esiste metto il dafault letto dal configDT
            self.redis.aset('DTmode',self.DTmode)

        if self.redis.esistetag(self.tags['DTmode_set'][0]) != 0:
            self.DTmod_set = self.tags['DTmode_set'][0]
        else:
            self.DTmode_set = self.tags['DTmode_set'][1] # se non esiste metto il dafault letto dal configDT
            self.redis.aset('DTmode_set',self.DTmode)



#         if self.redis.esistetag('DT:mode') != 0:
#             self.DTmode = self.redis.aget('DT:mode')
#         else:
#             self.DTmode = self.configDT['redis']['DT:mode'] # se non esiste metto il dafault letto dal configDT
#             self.redis.aset('DT:mode',self.DTmode)

#         if self.redis.esistetag('DT:mode_set') != 0:
# #            self.DTmode = self.redis.get('DTmode')
#             self.DTmode_set = self.redis.aget('DT:mode_set')
#         else:
#             self.DTmode_set = self.configDT['redis']['DT:mode_set'] # se non esiste metto il dafault letto dal configDT
#             self.redis.aset('DT:mode_set',self.DTmode_set)



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
            self.DTmode = self.redis.aget('DTmode')   # int(self.redis.get('DT:mode'))
        elif val == FORZSIM:
            self.DTmode = val
            self.redis.aset('DTmode',val)
        elif val == FORZLEARN:
            self.DTmode = val
            self.redis.aset('DTmode',val)
        
        #return time + 1   # se è hybrid o time-based
        return None     # se è event-base

    def get_data(self, outputs):
        logger.info('get_data with {outputs}, self.DTmode {DTmode}', outputs=outputs, DTmode=self.DTmode)
        return {self.eid: {'DTmode': self.DTmode}}
    
    def finalize(self):
        self.redis.chiudi()


def main():
    return mosaik_api_v3.start_simulation(DTSDA_Mng())

if __name__ == '__main__':
     main()