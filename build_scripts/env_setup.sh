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

cp ./docs/docker/Dockerfile ./build/build_scripts/

sed -i "s@FROM ubuntu:18.04@@g" ./build/build_scripts/Dockerfile
sed -i "s@WORKDIR /home/openharmony@@g" ./build/build_scripts/Dockerfile
sed -i "s@ENV LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8 LC_ALL=en_US.UTF-8@@g" ./build/build_scripts/Dockerfile

sed -i "s@RUN @@g" ./build/build_scripts/Dockerfile
sed -i "s@&& @@g" ./build/build_scripts/Dockerfile

sed -i "s@\t@@g" ./build/build_scripts/Dockerfile
sed -i "s@\\\@@g" ./build/build_scripts/Dockerfile


sed -i 's@ruby\S*\s@ruby @' ./build/build_scripts/Dockerfile
sed -i "s@python3.8-distutils@python3-distutils@g" ./build/build_scripts/Dockerfile
sed -i "s@git-core@git@g" ./build/build_scripts/Dockerfile
sed -i "s@zlib*@zlib@g" ./build/build_scripts/Dockerfile
sed -i "s@cd /home/openharmony@cd /../..@g" ./build/build_scripts/Dockerfile
sed -i '/pip3 install/i python3 -m pip install --user ohos-build' ./build/build_scripts/Dockerfile
sed -i '/pip3 install six/i pip3 install testresource' ./build/build_scripts/Dockerfile
sed -i 's@/root/.bashrc@/home/'$USER'/.bashrc@g' ./build/build_scripts/Dockerfile

result1=$(echo $SHELL | grep "bash")
result2=$(echo $SHELL | grep "zsh")

if [[ "$result1" != "" ]]
then
    sed -i "s@/root/.bashrc@~/.bashrc@g" ./build/build_scripts/Dockerfile 
elif [ [$result2 != ""] ]
then
    sed -i "s@/root/.bashrc@~/.zshrc@g" ./build/build_scripts/Dockerfile
else
    echo "Shell is not default, please configure the PATH variable manually"
fi


mv ./build/build_scripts/Dockerfile ./build/build_scripts/rundocker.sh
chmod +x ./build/build_scripts/rundocker.sh
sudo ./build/build_scripts/rundocker.sh
# rm ./build/build_scripts/rundocker.sh

if [[ "$result1" != "" ]]
then
    source ~/.bashrc
    
elif [[$result2 != ""]]
then
    source ~/.zshrc
else
    echo "Shell is not default, please configure the PATH variable manually"
fi




