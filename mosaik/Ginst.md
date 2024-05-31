# Set up di DTWIN, UBUNTU20.04
## preparazione sistema
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt install python3-pip
sudo apt install python3-virtualenv
sudo apt  install docker.io -y
sudo apt  install docker-compose -y
sudo usermod -aG docker $USER
sudo apt install redis-tools -y

## preparazione python
sudo apt install build-essential -y
sudo apt install swig -y
sudo apt install libsundials-dev -y
sudo apt install libboost-all-dev  -y
pip3 install -r requirements.txt

## set up servizi e utilità
### Visual studio code
sudo apt install software-properties-common apt-transport-https wget
### altri
sudo install gedit
sudo snap install mqtt-explorer
sudo cp -a docker/minio2     dt-rse-mosaik/mosaik/docker
sudo cp -a docker/influxdb   dt-rse-mosaik/mosaik/docker
sudo cp -a docker/mqtt        dt-rse-mosaik/mosaik/docker

sudo chown -R 1001:1001 redis-data/
sudo chown -R 1001:1001 minio-data/

