
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
