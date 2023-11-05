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
PYTHON3_DIR=${SOURCE_ROOT_DIR}/prebuilts/python/${HOST_DIR}/current/
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
npm config set lockfile false
cat $HOME/.npmrc | grep 'lockfile=false' || echo 'lockfile=false' >> $HOME/.npmrc

function init_ohpm() {
  TOOLS_INSTALL_DIR="${SOURCE_ROOT_DIR}/prebuilts/build-tools/common"
  pushd ${TOOLS_INSTALL_DIR}
    if [[ ! -f "${TOOLS_INSTALL_DIR}/oh-command-line-tools/ohpm/bin/ohpm" ]]; then
      echo "download oh-command-line-tools"
      wget https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/68/v3/r-5H8I7LT9mBjSFpSOY0Sg/ohcommandline-tools-linux-2.1.0.6.zip\?HW-CC-KV\=V1\&HW-CC-Date\=20231027T004601Z\&HW-CC-Expire\=315360000\&HW-CC-Sign\=A4D5E1A29C1C6962CA65592C3EB03ED363CE664CBE6C5974094064B67C34325E -O ohcommandline-tools-linux.zip
      unzip ohcommandline-tools-linux.zip
    fi
    OHPM_HOME=${TOOLS_INSTALL_DIR}/oh-command-line-tools/ohpm
    chmod +x ${OHPM_HOME}/bin/init
    echo "init ohpm"
    ${OHPM_HOME}/bin/init
    echo "ohpm version is $(ohpm -v)"
    ohpm config set registry https://repo.harmonyos.com/ohpm/
    ohpm config set strict_ssl false
    ohpm config set log_level debug
  popd
  if [[ -d "$HOME/.hvigor" ]]; then
    echo "remove $HOME/.hvigor"
    rm -rf $HOME/.hvigor/daemon $HOME/.hvigor/wrapper
  fi
  mkdir -p $HOME/.hvigor/wrapper/tools
  echo '{"dependencies": {"pnpm": "7.30.0"}}' > $HOME/.hvigor/wrapper/tools/package.json
  pushd $HOME/.hvigor/wrapper/tools
    echo "install pnpm"
    npm install
  popd
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
    SDK_PREBUILTS_PATH=${ROOT_PATH}/prebuilts/ohos-sdk

    pushd ${ROOT_PATH}
      echo "building the latest ohos-sdk..."
      ./build.py --product-name ohos-sdk --load-test-config=false --get-warning-list=false --stat-ccache=false --compute-overlap-rate=false --deps-guard=false --generate-ninja-trace=false --gn-args skip_generate_module_list_file=true sdk_platform=linux ndk_platform=linux use_cfi=false use_thin_lto=false enable_lto_O0=true sdk_check_flag=false enable_ndk_doxygen=false archive_ndk=false sdk_for_hap_build=true
      if [[ "$?" -ne 0 ]]; then
        echo "ohos-sdk build failed! You can try to use '--no-prebuilt-sdk' to skip the build of ohos-sdk."
        exit 1
      fi
      if [ -d "${ROOT_PATH}/prebuilts/ohos-sdk/linux" ]; then
          rm -rf ${ROOT_PATH}/prebuilts/ohos-sdk/linux
      fi
      mkdir -p ${SDK_PREBUILTS_PATH}
      mv ${ROOT_PATH}/out/sdk/ohos-sdk/linux ${SDK_PREBUILTS_PATH}/
      mkdir -p ${SDK_PREBUILTS_PATH}/linux/native
      mv ${ROOT_PATH}/out/sdk/sdk-native/os-irrelevant/* ${SDK_PREBUILTS_PATH}/linux/native/
      mv ${ROOT_PATH}/out/sdk/sdk-native/os-specific/linux/* ${SDK_PREBUILTS_PATH}/linux/native/
      pushd ${SDK_PREBUILTS_PATH}/linux
        api_version=$(grep apiVersion toolchains/oh-uni-package.json | awk '{print $2}' | sed -r 's/\",?//g') || api_version="11"
        mkdir -p $api_version
        for i in */; do
            if [ -d "$i" ] && [ "$i" != "$api_version/" ]; then
                mv $i $api_version
            fi
        done
      popd
    popd
}
if [[ ! -d "${SOURCE_ROOT_DIR}/prebuilts/ohos-sdk/linux" && "$*" != *ohos-sdk* && "$*" != *"--no-prebuilt-sdk"* || "${@}" =~ "--prebuilt-sdk" ]]; then
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
