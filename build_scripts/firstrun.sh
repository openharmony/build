# !/bin/bash
# 将docs/docker/Dockerfile复制到当前目录
cp ../../../docs/docker/Dockerfile ./
# 格式化复制过来的dockerfile为.sh格式
#删除前面两行
sed -i "s@FROM ubuntu:18.04@@g" ./Dockerfile
sed -i "s@WORKDIR /home/openharmony@@g" ./Dockerfile
#删除RUN
sed -i "s@RUN @@g" ./Dockerfile
sed -i "s@&& @@g" ./Dockerfile
#将windows换行符\与制表符删除
sed -i "s:\t::g" ./Dockerfile
sed -i "s:\\\::g" ./Dockerfile
# 重命名为rundocker.sh
mv Dockerfile rundocker.sh
# 添加可读可写可执行权限
chmod 777 rundocker.sh
# 执行dockerfile转换成sh之后的脚本
./rundocker.sh
# rm rundocker.sh


# 安装编译所需依赖环境
apt-get install unzip
apt-get install flex bison
apt-get install zip
apt-get install ruby
apt-get install openssl libssl-dev
apt install openjdk-8-jre-headless
apt-get install genext2fs


