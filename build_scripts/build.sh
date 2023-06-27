#!/bin/bash
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

set -e
set +e
echo "++++++++++++++++++++++++++++++++++++++++"
function check_shell_environment() {
  case $(uname -s) in 
    Linux)
          shell_result=$(/bin/sh -c 'echo ${BASH_VERSION}')
          if [ -n "${shell_result}" ]; then
            echo "The system shell is bash ${shell_result}"
          else
            echo -e "\033[33m Your system shell isn't bash, we recommend you to use bash, because some commands may not be supported in other shells, such as pushd and shopt are not supported in dash. \n You can follow these tips to modify the system shell to bash on Ubuntu: \033[0m"
            echo -e "\033[33m [1]:Open the Terminal tool and execute the following command: sudo dpkg-reconfigure dash \n [2]:Enter the password and select <no>  \033[0m"
          fi
          ;;
    Darwin)
          echo "Darwin system is not supported yet"
          ;;
    *)
          echo "Unsupported this system: $(uname -s)"
          exit 1
  esac
}

check_shell_environment 

echo "++++++++++++++++++++++++++++++++++++++++"
date +%F' '%H:%M:%S
echo $@

export SOURCE_ROOT_DIR=$(cd $(dirname $0);pwd)

while [[ ! -f "${SOURCE_ROOT_DIR}/.gn" ]]; do
    SOURCE_ROOT_DIR="$(dirname "${SOURCE_ROOT_DIR}")"
    if [[ "${SOURCE_ROOT_DIR}" == "/" ]]; then
        echo "Cannot find source tree containing $(pwd)"
        exit 1
    fi
done

if [[ "${SOURCE_ROOT_DIR}x" == "x" ]]; then
  echo "Error: SOURCE_ROOT_DIR cannot be empty."
  exit 1
fi

case $(uname -s) in
    Darwin)
        HOST_DIR="darwin-x86"
        HOST_OS="mac"
        NODE_PLATFORM="darwin-x64"
        ;;
    Linux)
        HOST_DIR="linux-x86"
        HOST_OS="linux"
        NODE_PLATFORM="linux-x64"
        ;;
    *)
        echo "Unsupported host platform: $(uname -s)"
        RET=1
        exit $RET
esac

# set python3
PYTHON3_DIR=${SOURCE_ROOT_DIR}/prebuilts/python/${HOST_DIR}/3.9.2/
PYTHON3=${PYTHON3_DIR}/bin/python3
PYTHON=${PYTHON3_DIR}/bin/python
if [[ ! -f "${PYTHON3}" ]]; then
  echo -e "\033[33m Please execute the build/prebuilts_download.sh \033[0m"
  exit 1
else
  if [[ ! -f "${PYTHON}" ]]; then
    ln -sf "${PYTHON3}" "${PYTHON}"
  fi
fi

export PATH=${SOURCE_ROOT_DIR}/prebuilts/build-tools/${HOST_DIR}/bin:${PYTHON3_DIR}/bin:$PATH

# set nodejs and ohpm
EXPECTED_NODE_VERSION="14.21.1"
export PATH=${SOURCE_ROOT_DIR}/prebuilts/build-tools/common/nodejs/node-v${EXPECTED_NODE_VERSION}-${NODE_PLATFORM}/bin:$PATH
export NODE_HOME=${SOURCE_ROOT_DIR}/prebuilts/build-tools/common/nodejs/node-v${EXPECTED_NODE_VERSION}-${NODE_PLATFORM}
export PATH=${SOURCE_ROOT_DIR}/prebuilts/build-tools/common/oh-command-line-tools/ohpm/bin:$PATH
echo "Current Node.js version is $(node -v)"
NODE_VERSION=$(node -v)
if [ "$NODE_VERSION" != "v$EXPECTED_NODE_VERSION" ]; then
  echo "Node.js version mismatch. Expected $EXPECTED_NODE_VERSION but found $NODE_VERSION" >&2
  exit 1
fi
echo "Node.js version check passed"
npm config set registry https://repo.huaweicloud.com/repository/npm/
npm config set @ohos:registry https://repo.harmonyos.com/npm/
npm config set strict-ssl false
npm config set package-lock false

function init_ohpm() {
  TOOLS_INSTALL_DIR="${SOURCE_ROOT_DIR}/prebuilts/build-tools/common"
  cd ${TOOLS_INSTALL_DIR}
  commandlineVersion=2.0.1.0
  if [[ ! -f "${SOURCE_ROOT_DIR}/prebuilts/build-tools/common/oh-command-line-tools/ohpm/bin/ohpm" ]]; then
    echo "download oh-command-line-tools"
    wget https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/a6/v3/cXARnGbKTt-4sPEi3GcnJA/ohcommandline-tools-linux-2.0.0.1.zip\?HW-CC-KV\=V1\&HW-CC-Date\=20230512T075353Z\&HW-CC-Expire\=315360000\&HW-CC-Sign\=C82B51F3C9F107AB460EC26392E25B2E20EF1A6CAD10A26929769B21B8C8D5B6 -O ohcommandline-tools-linux.zip
    unzip ohcommandline-tools-linux.zip
  fi
  OHPM_HOME=${TOOLS_INSTALL_DIR}/oh-command-line-tools/ohpm
  chmod +x ${OHPM_HOME}/bin/init
  echo "init ohpm"
  ${OHPM_HOME}/bin/init
  echo "ohpm version is $(ohpm -v)"
  ohpm config set registry https://repo.harmonyos.com/ohpm/
  ohpm config set strict_ssl false
  cd ${SOURCE_ROOT_DIR}
  if [[ -d "~/.hvigor" ]]; then
    rm -rf ~/.hvigor
  fi
}

if [[ "$*" != *ohos-sdk* ]]; then
  echo "start set ohpm"
  init_ohpm
  if [[ "$?" -ne 0 ]]; then
    echo "ohpm init failed!"
    exit 1
  fi
fi

function build_sdk() {
        ROOT_PATH=${SOURCE_ROOT_DIR}
        if [ -d ${ROOT_PATH}/out/sdk/packages/ohos-sdk/linux ]; then
                echo "ohos-sdk exists."
                return 0
        fi
        pushd ${ROOT_PATH}
        echo "building the latest ohos-sdk..."
        ./build.py --product-name ohos-sdk --get-warning-list=false --stat-ccache=false --compute-overlap-rate=false --deps-guard=false --generate-ninja-trace=false --gn-args skip_generate_module_list_file=true --gn-args sdk_platform=linux
        if [[ "$?" -ne 0 ]]; then
          echo "ohos-sdk build failed!"
          exit 1
        fi

        if [ -d ${ROOT_PATH}/out/sdk/packages/ohos-sdk/linux ]; then
            pushd ${ROOT_PATH}/out/sdk/packages/ohos-sdk/linux
            ls -d */ | xargs rm -rf
            for i in $(ls); do
                    unzip $i
            done
            for f in $(find . -name package.json); do
                    pushd $(dirname $f)
                    npm install
                    popd
            done
            api_version=$(grep apiVersion toolchains/oh-uni-package.json | awk '{print $2}' | sed -r 's/\",?//g')
            sdk_version=$(grep version toolchains/oh-uni-package.json | awk '{print $2}' | sed -r 's/\",?//g')
            for i in $(ls -d */); do
                    mkdir -p $api_version
                    mv $i $api_version
                    mkdir $i
                    ln -s ../$api_version/$i $i/$sdk_version
            done
            popd
        fi
        popd
}
if [[ ! -d "${SOURCE_ROOT_DIR}/out/sdk/packages/ohos-sdk/linux" && "$*" != *ohos-sdk* && "$*" != *"--no-prebuilt-sdk"* ]]; then
  echo "start build ohos-sdk"
  build_sdk
  if [[ "$?" -ne 0 ]]; then
    echo "ohos-sdk build failed, please remove the out/sdk directory and try again!"
    exit 1
  fi
fi

${PYTHON3} ${SOURCE_ROOT_DIR}/build/scripts/tools_checker.py

flag=true
args_list=$@
for var in $@
do
  OPTIONS=${var%%=*}
  PARAM=${var#*=}
  if [[ "$OPTIONS" == "using_hb_new" && "$PARAM" == "false" ]]; then
    flag=false
    ${PYTHON3} ${SOURCE_ROOT_DIR}/build/scripts/entry.py --source-root-dir ${SOURCE_ROOT_DIR} $args_list
    break
  fi
done
if [[ ${flag} == "true" ]]; then
  ${PYTHON3} ${SOURCE_ROOT_DIR}/build/hb/main.py build $args_list
fi

if [[ "$?" -ne 0 ]]; then
    echo -e "\033[31m=====build ${product_name} error=====\033[0m"
    exit 1
fi
echo -e "\033[32m=====build ${product_name} successful=====\033[0m"

date +%F' '%H:%M:%S
echo "++++++++++++++++++++++++++++++++++++++++"
