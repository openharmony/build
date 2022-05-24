# !/bin/bash
cp ../../docs/docker/Dockerfile ./
sed -i "s@FROM ubuntu:18.04@@g" ./Dockerfile
sed -i "s@WORKDIR /home/openharmony@@g" ./Dockerfile
sed -i "s@RUN @@g" ./Dockerfile
sed -i "s@&& @@g" ./Dockerfile
sed -i "s:\t::g" ./Dockerfile
sed -i "s:\\\::g" ./Dockerfile
mv Dockerfile rundocker.sh
chmod a+x rundocker.sh
./rundocker.sh
apt-get install unzip
apt-get install flex bison
apt-get install zip
apt-get install ruby
apt-get install openssl libssl-dev
apt-get install openjdk-8-jre-headless
apt-get install genext2fs
apt-get install u-boot-tools -y
apt-get install mtools



