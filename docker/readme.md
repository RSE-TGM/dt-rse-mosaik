
# DT SDA comandi utili

### build esempio
docker build -t dtsda310 --file Dockerfile_python310 .
### lancio di docker compose
sudo docker-compose up -d
### cambiare nome image:
sudo docker image tag 013cdf9f0f21 aguagliardi/dtsda:latest
### push in dockerhub:
docker push aguagliardi/dtsda:latest
### lancio di una shell nel container
sudo docker run --name DTSDA -it   --rm aguagliardi/dtsda bash
sudo docker run --name DTSDA -it   --rm -v "/home/antonio/dtwin/dt-rse-mosaik:/home/dt-rse-mosaik" aguagliardi/dtsda bash
### attach ad un container in run ed esecuzione di bash
sudo docker exec -it DTSDA bash
### test del DT con fmi e plot gui
export DISPLAY=:0
xhost +
sudo docker exec -it DTSDA python3 mosaik/ScenarioDT_with_fmi.py
### pulizia dei container stoppati
docker rm $(docker ps --filter status=exited -q)
### creazione del network locale ai container
docker network create DT-net
### start di unsolo servizio in backgroud
docker-compose -f docker-compose_conRedis.yaml up -d DTredis
### attach dell'output di quel servizio
docker-compose -f docker-compose_conRedis.yaml logs
### restart di un servizio
docker-compose -f docker-compose_conRedis.yaml restart DTredis

### Apertura console MinIO
locale:
127.0.0.1:9090
user: admin
password: password

remoto:
http://172.25.102.102:9090/
user: admin
password: password

comandi a DT:   mqtt-explorer oppure mqttx
