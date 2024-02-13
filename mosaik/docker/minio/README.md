# Sistema Di Accumulo Digital Twin

Interfaccia di comunicazione con un dispositivo di accumulo

![img/schema.png](img.png)

# Descrizione ad alto livello 

Un DT-SDA rappresenta quindi un modello virtuale della batteria 
che include tutte le sue caratteristiche rilevanti, quali dimensioni, forma, capacità e stato di carica attuale. 
Il gemello digitale viene aggiornato in tempo reale man mano che la batteria fisica viene utilizzata e caricata,
consentendo a progettisti e operatori di monitorarne le prestazioni e il degrado nel tempo, nonché fare previsioni
sul suo comportamento. Queste informazioni possono essere utilizzate per ottimizzare il design della batteria, 
migliorarne l'affidabilità e prolungarne la durata. Inoltre, un gemello digitale di una batteria può essere utilizzato 
in simulazioni e ambienti di test virtuali, consentendo agli operatori ed ai progettisti di sperimentare diversi
parametri di progettazione e funzionamento senza la necessità di prototipi fisici.

Azioni richieste:
-   Caratteristiche asset


# Componenti

Le componenti pensate sono:
-   modello digitale
- tool di analisi
- dati dei sensori
- interazione con utente
- Dati fisici stati e parametri del modello

I dati del modello potrebbero essere messi in un S3 like opensource come minio
Minio è una soluzione di Object Storage compatibile con S3
https://quay.io/repository/minio/minio?tab=tags


![img/img.png](img.png)