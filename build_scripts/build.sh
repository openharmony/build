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
echo -e "\n\033[32m\t*********Welcome to OpenHarmony!*********\033[0m\n"
echo -e "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
function check_shell_environment() {
  case $(uname -s) in 
    Linux)
          shell_result=$(/bin/sh -c 'echo ${BASH_VERSION}')
          if [ -n "${shell_result}" ]; then
            echo -e "\033[32mSystem shell: bash ${shell_result}\033[0m"
          else
            echo -e "\033[33m Your system shell isn't bash, we recommend you to use bash, because some commands may not be supported in other shells, such as pushd and shopt are not supported in dash. \n You can follow these tips to modify the system shell to bash on Ubuntu: \033[0m"
            echo -e "\033[33m [1]:Open the Terminal tool and execute the following command: sudo dpkg-reconfigure dash \n [2]:Enter the password and select <no>  \033[0m"
          fi
          ;;
    Darwin)
          echo -e "\033[31m[OHOS ERROR] Darwin system is not supported yet\033[0m"
          ;;
    *)
          echo -e "\033[31m[OHOS ERROR] Unsupported this system: $(uname -s)\033[0m"
          exit 1
  esac
}

check_shell_environment 

echo -e "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo -e "\033[32mCurrent time: $(date +%F' '%H:%M:%S)\033[0m"
echo -e "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo -e "\033[32mBuild args: $@\033[0m"
echo -e "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

export SOURCE_ROOT_DIR=$(cd $(dirname $0);pwd)

while [[ ! -f "${SOURCE_ROOT_DIR}/.gn" ]]; do
    SOURCE_ROOT_DIR="$(dirname "${SOURCE_ROOT_DIR}")"
    if [[ "${SOURCE_ROOT_DIR}" == "/" ]]; then
        echo -e "\033[31m[OHOS ERROR] Cannot find source tree containing $(pwd)\033[0m"
        exit 1
    fi
done

if [[ "${SOURCE_ROOT_DIR}x" == "x" ]]; then
  echo -e "\033[31m[OHOS ERROR] SOURCE_ROOT_DIR cannot be empty.\033[0m"
  exit 1
fi

case $(uname -m) in
    *x86_64)
        host_cpu=x86_64
        host_cpu_prefix="x86"
        python_prefix="x86"
        node_prefix="x64"
        ;;
    *arm* | *aarch64)
        host_cpu=arm64
        host_cpu_prefix="aarch64"
        python_prefix="arm64"
        node_prefix="aarch64"
        ;;
    *)
        echo "\033[31m[OHOS ERROR] Unsupported host arch: $(uname -m)\033[0m"
        RET=1
        exit $RET
esac

case $(uname -s) in
    Darwin)
        HOST_DIR="darwin-$host_cpu_prefix"
        PYTHON_DIR="darwin-$python_prefix"
        HOST_OS="mac"
        NODE_PLATFORM="darwin-x64"
        ;;
    Linux)
        HOST_DIR="linux-$host_cpu_prefix"
        PYTHON_DIR="linux-$python_prefix"
        HOST_OS="linux"
        NODE_PLATFORM="linux-$node_prefix"
        ;;
    *)
        echo "\033[31m[OHOS ERROR] Unsupported host platform: $(uname -s)\033[0m"
        RET=1
        exit $RET
esac

# set python3
PYTHON3_DIR=$(realpath ${SOURCE_ROOT_DIR}/prebuilts/python/${PYTHON_DIR}/*/ | tail -1)
PYTHON3=${PYTHON3_DIR}/bin/python3
PYTHON=${PYTHON3_DIR}/bin/python
if [[ ! -f "${PYTHON3}" ]]; then
  echo -e "\033[31m[OHOS ERROR] Please execute the build/prebuilts_download.sh \033[0m"
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
echo "[OHOS INFO] Current Node.js version is $(node -v)"
NODE_VERSION=$(node -v)
if [ "$NODE_VERSION" != "v$EXPECTED_NODE_VERSION" ]; then
  echo -e "\033[31m[OHOS ERROR] Node.js version mismatch. Expected $EXPECTED_NODE_VERSION but found $NODE_VERSION\033[0m" >&2
  exit 1
fi
echo -e "\033[32m[OHOS INFO] Node.js version check passed!\033[0m"
npm config set registry https://repo.huaweicloud.com/repository/npm/
npm config set @ohos:registry https://repo.harmonyos.com/npm/
npm config set strict-ssl false
npm config set lockfile false
cat $HOME/.npmrc | grep 'lockfile=false' > /dev/null || echo 'lockfile=false' >> $HOME/.npmrc > /dev/null

function init_ohpm() {
  TOOLS_INSTALL_DIR="${SOURCE_ROOT_DIR}/prebuilts/build-tools/common"
  pushd ${TOOLS_INSTALL_DIR} > /dev/null
    OHPM_HOME=${SOURCE_ROOT_DIR}/prebuilts/command-line-tools/ohpm/bin
    chmod +x ${OHPM_HOME}/ohpm
    export PATH=${OHPM_HOME}:$PATH
    chmod +x ${OHPM_HOME}/init
    ${OHPM_HOME}/init > /dev/null
    echo "[OHOS INFO] Current ohpm version is $(ohpm -v)"
    ohpm config set registry https://repo.harmonyos.com/ohpm/
    ohpm config set strict_ssl false
    ohpm config set log_level debug
  popd > /dev/null
  if [[ -d "$HOME/.hvigor" ]]; then
    rm -rf $HOME/.hvigor/daemon $HOME/.hvigor/wrapper
  fi
  mkdir -p $HOME/.hvigor/wrapper/tools
  echo '{"dependencies": {"pnpm": "7.30.0"}}' > $HOME/.hvigor/wrapper/tools/package.json
  pushd $HOME/.hvigor/wrapper/tools > /dev/null
    echo "[OHOS INFO] installing pnpm..."
    npm install --silent > /dev/null
  popd > /dev/null
  mkdir -p $HOME/.ohpm
  echo '{"devDependencies":{"@ohos/hypium":"1.0.6"}}' > $HOME/.ohpm/oh-package.json5
  pushd $HOME/.ohpm > /dev/null
    echo "[OHOS INFO] installing hypium..."
    ohpm install > /dev/null
  popd > /dev/null
}

if [[ "$*" != *ohos-sdk* ]]; then
  echo "[OHOS INFO] Ohpm initialization started..."
  init_ohpm
  if [[ "$?" -ne 0 ]]; then
    echo -e "\033[31m[OHOS ERROR] ohpm initialization failed!\033[0m"
    exit 1
  fi
  echo -e "\033[32m[OHOS INFO] ohpm initialization successful!\033[0m"
fi
echo -e "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"

echo -e "\033[32m[OHOS INFO] Start building...\033[0m\n"
api_version=$(grep 'api_version =' build/version.gni | awk -F'"' '{print $2}' | sed -r 's/\"//g')
function build_sdk() {
    ROOT_PATH=${SOURCE_ROOT_DIR}
    SDK_PREBUILTS_PATH=${ROOT_PATH}/prebuilts/ohos-sdk

    pushd ${ROOT_PATH} > /dev/null
      echo -e "[OHOS INFO] building the latest ohos-sdk..."
      ./build.py --product-name ohos-sdk $ccache_args $xcache_args --load-test-config=false --get-warning-list=false --stat-ccache=false --compute-overlap-rate=false --deps-guard=false --generate-ninja-trace=false --gn-args skip_generate_module_list_file=true sdk_platform=linux ndk_platform=linux use_cfi=false use_thin_lto=false enable_lto_O0=true sdk_check_flag=false enable_ndk_doxygen=false archive_ndk=false sdk_for_hap_build=true enable_archive_sdk=false enable_notice_collection=false enable_process_notice=false --gn-args=sdk_build_arkts=true 
      if [[ "$?" -ne 0 ]]; then
        echo -e "\033[31m[OHOS ERROR] ohos-sdk build failed! You can try to use '--no-prebuilt-sdk' to skip the build of ohos-sdk.\033[0m"
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
      pushd ${SDK_PREBUILTS_PATH}/linux > /dev/null
        api_version=$(grep apiVersion toolchains/oh-uni-package.json | awk '{print $2}' | sed -r 's/\",?//g') || api_version="11"
        mkdir -p $api_version
        for i in */; do
            if [ -d "$i" ] && [ "$i" != "$api_version/" ]; then
                mv $i $api_version
            fi
        done
        pushd $api_version/ets/ > /dev/null
          for dir in ./ets1.1/*/; do 
            dir_name=$(basename "$dir")
            ln -s "./ets1.1/$dir_name" "$dir_name"
          done
        popd > /dev/null
      popd > /dev/null
      # 临时添加，因为xts编译失败无法归档ohos-sdk，输出ohos-sdk的md5值，用于验证OHOS-SDK生成是否存在概率问题
      pushd ${ROOT_PATH}/prebuilts/ohos-sdk/linux/${api_version} > /dev/null
        find -type f | sort | xargs md5sum
      popd > dev/null
    popd > /dev/null
}
function get_api(){
  current_dir=$(pwd)
  if [ -d "$current_dir/prebuilts/ohos-sdk-12/ohos-sdk/linux/12" ]; then
    mkdir -p $current_dir/prebuilts/ohos-sdk/linux/12
    mv "$current_dir/prebuilts/ohos-sdk-12/ohos-sdk/linux/12/"* "$current_dir/prebuilts/ohos-sdk/linux/12/"
  fi
}
if [[ ! -d "${SOURCE_ROOT_DIR}/prebuilts/ohos-sdk/linux/${api_version}" && "$*" != *ohos-sdk* && "$*" != *"--no-prebuilt-sdk"* || "${@}" =~ "--prebuilt-sdk" ]]; then
  echo -e "\033[33m[OHOS INFO] The OHOS-SDK was not detected, so the SDK compilation will be prioritized automatically. You can also control whether to execute this process by using '--no-prebuilt-sdk' and '--prebuilt-sdk'.\033[0m"
  if [[ "${@}" =~ "--ccache=false" || "${@}" =~ "--ccache false" ]]; then
    ccache_args="--ccache=false"
  else
    ccache_args="--ccache=true"
  fi
  if [[ "${@}" =~ "--xcache=true" || "${@}" =~ "--xcache true" || "${@}" =~ "--xcache" ]]; then
    xcache_args="--xcache=true"
  else
    xcache_args="--xcache=false"
  fi
  build_sdk
  target_dir="${SOURCE_ROOT_DIR}/prebuilts/ohos-sdk/linux/${api_version}/previewer"
  if [ ! -d "${target_dir}" ]; then
    mkdir "${target_dir}"
    cp -r "${SOURCE_ROOT_DIR}/prebuilts/ohos-sdk/linux/${api_version}/native/oh-uni-package.json" "${target_dir}/"
    sed -i 's/Native/Previewer/g' "${target_dir}/oh-uni-package.json"
    sed -i 's/native/previewer/g' "${target_dir}/oh-uni-package.json"
  fi
  get_api
  if [[ "$?" -ne 0 ]]; then
    echo -e "\033[31m[OHOS ERROR] ohos-sdk build failed, please remove the out/sdk directory and try again!\033[0m"
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
