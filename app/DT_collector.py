
# ## Data Collector
# Here is the complete file of the data collector:

"""
Semplice data collector che salva e stampa tutte le variabili alla fine della simulazione e scrive su una hash table di redis.
La scrittura su redis viene sempre eseguita ad ogni passo, mentre il salvataggio e la stampa finale è condizionata dalla variabile saveHistory.

"""
import collections

import mosaik_api_v3 as mosaik_api
from mosaik_api.datetime import Converter

from  DT_include import redisDT


META_Monitor = {
    'type': 'event-based',
    'models': {
        'Monitor': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
            # 'attrs': ['Tempoacq',
            #           'VAR1',
            #           'VAR2',
            #           'VAR3',
            #           'VAR4',
            #           'VAR5',
            #           'VAR6',
            #           'VAR7',
            #           'VAR8',
            #           'VAR9',
            #           'VAR10']
        },
    },
}


class Collector(mosaik_api.Simulator):
    """
        Semplice data collector che può salvare e stampare tutte le variabili alla fine della simulazione e scrive su una hash table di redis con lo stato delle variabili più rilevanti.
        La scrittura su redis viene sempre eseguita ad ogni passo, mentre il salvataggio e la stampa finale è condizionata dalla variabile saveHistory.
    """
    def __init__(self):
        super().__init__(META_Monitor)
        self.eid = None
        self.data = collections.defaultdict(lambda:
                                            collections.defaultdict(dict))
        
        self.redis = redisDT()     # legge il file di configurazione e crea oggetto redis  
        self.tags = self.redis.gettags()
        self.r = self.redis.connect()
        self.stream_name = self.tags['RefBatt']
        self.stream_name_config= self.tags['RefBattDIM']
  

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
        """Ad ogni step di calcolo salva in Redis lo stato della simulazione costituito da un prescelto set di variabili in inputs

        Args:
            time (int): Tempo corrente dela simulazione
            inputs (dict): Struttura che contiene le variabili calcolate, al tempo corrente, della simulazione (time)
            max_advance (int): massima attesa di tempo entro cui lanciare il metodo step, non usato attualmente

        Returns:
            None: -
        """               
        data = inputs.get(self.eid, {})

        # Salvo lo stato della simulazione su Redis
        if "local_time" in data:
            timestamp = next(iter(data["local_time"].values()))
            print(f"collector: timestamp={timestamp} ")
        elif self._time_converter:
            timestamp: str = self._time_converter.isoformat_from_step(time) # timestamp in formato testo 
            timestamp_ms = int(self._time_converter.datetime_from_step(time).timestamp()*1000) # timestamp in ms, tipo int

        self.redis.aset('tsim',str(time), hmode=True)
        self.redis.aset('timestamp',str(timestamp), hmode=True)
        self.redis.aset('timestamp_ms',str(timestamp_ms), hmode=True)
        
        for attr, values in data.items():
            for src, value in values.items():
                if self.saveHistory: self.data[src][attr][time] = value
                #savetoredis(src,attr,time,value)                
                if attr != 'DTmode' and attr != 'DTmode_set' : 
                    valueApross='%.3f' % round(value * 1000 / 1000,3)  # 3 decimali
                    self.redis.aset(attr,str(valueApross), hmode=True)
        # futuro?? Leggo da redis il valore delle variabili della batteria vera per  l'invio a influxDB
        # stream_name_ind = int(self.r.get(self.stream_name_config)) - 1    # se DIM è 100 allora 99 è il più recente
        # lastStream=self.redis.readstream(self.stream_name, stream_name_ind) # è un dict e contiene i valori più recenti delle variabili di interesse della batteria vera lette da Redis come  stream
        
        return None
    
    def finalize(self):
        """Alla fine della simulazione, 
        se la variabile 'saveHistory' è attivata, vengono stampati su terminale il valore delle variabili calcolate
        """        
        if self.saveHistory: 
            print('Collected data:')
            for sim, sim_data in sorted(self.data.items()):
                print('- %s:' % sim)
                for attr, values in sorted(sim_data.items()):
                    print('  - %s: %s' % (attr, values))

if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
