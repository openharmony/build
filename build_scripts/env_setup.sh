# !/bin/bash
# Copy ../../docs/docker/Dockerfile to the current directory and format Dockerfile and rename it rundocker.sh
# Execute rundocker.sh and install other required dependencies

cp ../../docs/docker/Dockerfile ./
sed -i "s@FROM ubuntu:18.04@@g" ./Dockerfile
sed -i "s@WORKDIR /home/openharmony@@g" ./Dockerfile
sed -i "s@RUN @@g" ./Dockerfile
sed -i "s@&& @@g" ./Dockerfile
sed -i "s:\t::g" ./Dockerfile
sed -i "s:\\\::g" ./Dockerfile
mv Dockerfile rundocker.sh
chmod 777 rundocker.sh
./rundocker.sh
# rm rundocker.sh


#  Compilation rk3568 required
apt-get install unzip
apt-get install flex bison
apt-get install zip
apt-get install ruby
apt-get install openssl libssl-dev
apt-get install openjdk-8-jre-headless
apt-get install genext2fs
# Compilation hispark_taurus_standard(3516) required
apt-get install u-boot-tools -y

# Compilation ipcamera_hispark_taurus_linux required
apt-get install mtools



