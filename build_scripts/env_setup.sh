# !/bin/bash

# Copyright (c) 2021 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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



