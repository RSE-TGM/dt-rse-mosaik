# minio mc client install
curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  --create-dirs \
  -o $HOME/minio-binaries/mc

https://min.io/docs/minio/linux/reference/minio-mc.html#
chmod +x $HOME/minio-binaries/mc
export PATH=$PATH:$HOME/minio-binaries/
mc --help

export ALIAS=dtminio
export HOSTNAME=http://127.0.0.1:9090/
export ACCESS_KEY=oouICbtT7IsE0HQpmVWg
export SECRET_KEY=8DvNcONsS0TwoCbiuLHdZDxoWgS0IxeQKOqkR1Pv
mc alias set $ALIAS $HOSTNAME $ACCESS_KEY $SECRET_KEY

esempio comandi:
mc admin info dtminio
mc ping dtminio
mc put docker-compose.yml dtminio/sda-dt
mc cp --recursive configuration dtminio/sda-dt/conf
mc cp --recursive dtminio/sda-dt/conf conf1

save configurazione (verso minio):
mc cp --recursive configuration dtminio/sda-dt/conf1
reload configurazione (da minio al file system):
mc cp --recursive dtminio/sda-dt/conf1/configuration .
