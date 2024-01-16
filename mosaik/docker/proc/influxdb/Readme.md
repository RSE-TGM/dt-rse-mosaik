
istruzioni:
https://hub.docker.com/_/influxdb

# Installazione influxdb
```
mkdir data
mkdir config
docker network create  DT-net
docker-compose up -d

```

## Configurazione da CLI

```
docker exec -it influxdb_influxdb_1  /bin/bash
```

## Configurazione da browser

```
http://localhost:8086/
```
## Credenziali
```
user: influxuser
password: DTpass!!
Organisation: RSE

Bucket: multiBuck
```
