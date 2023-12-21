
# DT SDA comandi utili

## lancio di docker compose
sudo docker-compose up -d
## cambiato nome image:
sudo docker image tag 013cdf9f0f21 aguagliardi/dtsda:latest
## push in dockerhub:
docker push aguagliardi/dtsda:latest
## lancio di una shell sul container
sudo docker run --name DTsda -it   --rm aguagliardi/dtsda bash
## attach ad un container in run
sudo docker exec -it DTSDA bash
