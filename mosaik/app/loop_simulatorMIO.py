"""
Mosaik interface for the example simulator.

It more complex than it needs to be to be more flexible and show off various
features of the mosaik API.

"""
from loguru import logger

import mosaik_api_v3


example_sim_meta = {
    'type': 'hybrid',
    'models': {'DTSDAMng': {'public': True,
                     'params': [],
                     'attrs': ['DTmode_set', 'DTmode'],
                     'trigger': ['DTmode_set'],
                     'non-persistent': ['DTmode'],
                     },
               }
}


class DTSDA_Mng(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(example_sim_meta)
        self.sid = None
        self.eid = None
        self.step_size = None
        self.self_steps = None
        self.loop_count = 0
        self.loop_length = None

    def init(self, sid, time_resolution, step_size=1, self_steps=None,
             loop_length=0):
        self.sid = sid
        self.step_size = step_size
        self.loop_length = loop_length
        return self.meta

    def create(self, num, model):
        self.eid = 'DTSDAMng1'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        self.time = time

        self.loop_count += 1

        if self.loop_count == self.loop_length + 1:
            next_step = time + self.step_size
            self.loop_count = 0
        else:
            next_step = None
        logger.info('step at {time}, next step at {next_step}', time=time, 
                    next_step=next_step)
        return next_step

    def get_data(self, outputs):
        if self.loop_count == 0:
            data = {}
        else:
            data = {self.eid: {'DTmode': self.loop_count}}
        logger.info('get_data at {time}, returning {data}', 
                    time=self.time, data=data)

        return data


def main():
    return mosaik_api_v3.start_simulation(DTSDA_Mng())
