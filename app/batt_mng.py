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
        self.DTmodeSTR=''
        self.DTmode_set = None
        self.DTmode_setSTR = ''
        self.redis = None

    def init(self, sid, time_resolution):
        self.sid = sid

        #connessione a Redis, in fase di test su localhost
        self.redis = redisDT()     # legge il file di configurazione e crea oggetto redis  
        self.tags = self.redis.gettags()
        self.r = self.redis.connect()
        

        if self.redis.esistetag('DTmode') != 0:
 #       if self.redis.esistetag(self.tags['DTmode'][0]) != 0:
            self.DTmodeSTR=self.redis.aget('DTmode')
            self.DTmode = hash(self.DTmodeSTR)  # se esiste, leggo il valore da redis
 #           self.DTmode = self.redis.aget(self.tags['DTmode'][0])  # se esiste, leggo il valore da redis
        else:
            self.DTmodeSTR = hash(self.tags['DTmode'][1])        # se non esiste metto leggo il val
            self.redis.aset('DTmode',self.DTmodeSTR ) # se non esiste metto il dafault letto dal configDT anche in redis
#            self.redis.aset('DTmode',self.DTmode)

        if self.redis.esistetag('DTmode_set') != 0:
#        if self.redis.esistetag(self.tags['DTmode_set'][0]) != 0:
            self.DTmod_setSTR = self.redis.aget('DTmode_set')  # se esiste, leggo il valore da redis
            self.DTmod = hash(self.DTmod_setSTR)
#            self.DTmod_set = self.redis.aget(self.tags['DTmode_set'][0])  # se esiste, leggo il valore da redis
        else:
            self.DTmode_setSTR = hash(self.tags['DTmode_set'][1])       # se esiste, leggo il valore da rediss
            self.redis.aset('DTmode_set',self.DTmode_setSTR) # se non esiste metto il dafault letto dal configDT



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
        val=list(inputs[self.eid]['DTmode_set'].values())[0]
        

        # match val:
        #     case NOFORZ:
        #         self.DTmode = int(self.redis.get('DT:mode'))                
        #     case FORZSIM:
        #         self.redis.set('DT:mode',self.redis.set('DT:mode',val))
        #     case _:
        # val = NOFORZ
        if val == NOFORZ :
            self.DTmodeSTR = self.redis.aget('DTmode')
            self.DTmode = hash(self.DTmodeSTR)  # int(self.redis.get('DT:mode'))
        elif val == FORZSIM:
            self.DTmode = val
            self.DTmodeSTR = S_SIM
            self.redis.aset('DTmode',S_SIM)
        elif val == FORZLEARN:
            self.DTmode = val
            self.DTmodeSTR = S_LEARN
            self.redis.aset('DTmode',S_LEARN)
        
        logger.info('step at {time} with inputs {inputs}, DTmode_set={DTmode_set}', time=time, inputs=inputs, DTmode_set=self.DTmodeSTR)
        #return time + 1   # se è hybrid o time-based
        return None     # se è event-base

    def get_data(self, outputs):
        logger.info('get_data with {outputs}, self.DTmode {DTmode}', outputs=outputs, DTmode=self.DTmodeSTR)
        return {self.eid: {'DTmode': self.DTmode}}
    
    def finalize(self):
        self.redis.chiudi()


def main():
    return mosaik_api_v3.start_simulation(DTSDA_Mng())

if __name__ == '__main__':
     main()