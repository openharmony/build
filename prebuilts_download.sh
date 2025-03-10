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

script_path=$(cd $(dirname $0);pwd)
code_dir=$(dirname ${script_path})

if [[ "${@}" =~ "--tool-repo" && -f "${code_dir}/prebuilts.sh" ]]; then
    # prebuilts.sh should be a symbolic link to a prebuilts_download.sh created by oneself.
    bash ${code_dir}/prebuilts.sh $@
else
while [ $# -gt 0 ]; do
  case "$1" in
    -skip-ssl|--skip-ssl) # wget、npm skip ssl check, which will allow
                          # hacker to get and modify data stream between server and client!
    SKIP_SSL=YES
    ;;
    -h|--help)
    HELP=YES
    ;;
    --disable-rich)       # disable the rich module of python
    DISABLE_RICH=YES
    ;;
    --enable-symlink)     # enable symlink while copying node_modules
    ENABLE_SYMLINK=YES
    ;;
    --build-arkuix)
    BUILD_ARKUIX=YES
    ;;
    --tool-repo)
    TOOL_REPO="$2"
    shift
    ;;
    --tool-repo=*)
    TOOL_REPO="${1#--tool-repo=}"
    ;;
    --npm-registry)
    NPM_REGISTRY="$2"
    shift
    ;;
    --npm-registry=*)
    NPM_REGISTRY="${1#--npm-registry=}"
    ;;
    --trusted-host)
    TRUSTED_HOST="$2"
    shift
    ;;
    --trusted-host=*)
    TRUSTED_HOST="${1#--trusted-host=}"
    ;;
    --pypi-url)           # python package index url
    PYPI_URL="$2"
    shift
    ;;
    --pypi-url=*)
    PYPI_URL="${1#--pypi-url=}"
    ;;
    --download-sdk)       # Download the SDK if this flag is set
    DOWNLOAD_SDK=YES
    ;;
    *)
    echo "$0: Warning: unsupported parameter: $1" >&2
    ;;
  esac
  shift
done

case $(uname -s) in
    Linux)
        host_platform=linux
        glibc_version=$(getconf GNU_LIBC_VERSION | grep -oE '[0-9].[0-9]{2}')
        ;;
    Darwin)
        host_platform=darwin
        ;;
    *)
        echo "Unsupported host platform: $(uname -s)"
        exit 1
esac

case $(uname -m) in
    arm64)
        host_cpu=arm64
        host_cpu_prefix=arm64
        ;;
    aarch64)
        host_cpu=arm64
        host_cpu_prefix=aarch64
        ;;
    *)
        host_cpu=x86_64
        host_cpu_prefix=x86
esac

if [ "X${SKIP_SSL}" == "XYES" ];then
    wget_ssl_check="--skip-ssl"
else
    wget_ssl_check=''
fi

if [ "X${HELP}" == "XYES" ];then
    help="-h"
else
    help=''
fi

if [ "X${ENABLE_SYMLINK}" == "XYES" ];then
    enable_symlink="--enable-symlink"
else
    enable_symlink=''
fi

if [ ! -z "$TOOL_REPO" ];then
    tool_repo="--tool-repo $TOOL_REPO"
else
    tool_repo=''
fi

if [ ! -z "$NPM_REGISTRY" ];then
    npm_registry="--npm-registry $NPM_REGISTRY"
else
    npm_registry=''
fi

if [ ! -z "$TRUSTED_HOST" ];then
    trusted_host=$TRUSTED_HOST
elif [ ! -z "$PYPI_URL" ];then
    trusted_host=${PYPI_URL/#*:\/\//}       # remove prefix part such as http:// https:// etc.
    trusted_host=${trusted_host/%[:\/]*/}   # remove suffix part including the port number
else
    trusted_host='repo.huaweicloud.com'
fi

if [ ! -z "$PYPI_URL" ];then
    pypi_url=$PYPI_URL
else
    pypi_url='http://repo.huaweicloud.com/repository/pypi/simple'
fi

if [ $UID -ne 0 ]; then
    npm_para=''
else
    npm_para='--unsafe-perm'
fi

if [ "X${BUILD_ARKUIX}" == "XYES" ];then
    build_arkuix="--build-arkuix"
else
    build_arkuix=''
fi

if [ "X${DISABLE_RICH}" == "XYES" ];then
  disable_rich='--disable-rich'
else
  set +e
  pip3 install --trusted-host $trusted_host -i $pypi_url rich;
  if [ $? -eq 0 ];then
      echo "rich installed successfully"
  else
      disable_rich='--disable-rich'
  fi
  set -e
fi

cpu="--host-cpu $host_cpu"
platform="--host-platform $host_platform"
if [[ "${glibc_version}" < "2.35" ]]; then
    glibc_version="--glibc-version GLIBC2.27"
else
    glibc_version="--glibc-version GLIBC2.35"
fi
echo "prebuilts_download start"
if [ -d "${code_dir}/prebuilts/build-tools/common/nodejs" ];then
    rm -rf "${code_dir}/prebuilts/build-tools/common/nodejs"
    echo "remove nodejs"
fi
python3 "${code_dir}/build/prebuilts_download.py" $wget_ssl_check $tool_repo $npm_registry $help $cpu $platform $npm_para $disable_rich $enable_symlink $build_arkuix $glibc_version
if [ -f "${code_dir}/prebuilts/cmake/linux-${host_cpu_prefix}/bin/ninja" ];then
    rm -rf "${code_dir}/prebuilts/cmake/linux-${host_cpu_prefix}/bin/ninja"
fi
if [ -f "${code_dir}/prebuilts/cmake/windows-x86/bin/ninja.exe" ];then
    rm -rf "${code_dir}/prebuilts/cmake/windows-x86/bin/ninja.exe"
fi
if [ -f "${code_dir}/prebuilts/cmake/darwin-universal/bin/ninja" ];then
    rm -rf "${code_dir}/prebuilts/cmake/darwin-universal/bin/ninja"
fi
echo "remove ninja in cmake"
echo "prebuilts_download end"

PYTHON_PATH=$(realpath $code_dir/prebuilts/python/${host_platform}-${host_cpu_prefix}/*/bin | tail -1)

if [[ "${host_platform}" == "linux" ]]; then
    sed -i "1s%.*%#!/usr/bin/env python3%" "${PYTHON_PATH}/pip3"
elif [[ "${host_platform}" == "darwin" ]]; then
    sed -i "" "1s%.*%#!/usr/bin/env python3%" "${PYTHON_PATH}/pip3"
fi
prebuild_python3_path="${PYTHON_PATH}/python3"
prebuild_pip3_path="${PYTHON_PATH}/pip3"
$prebuild_python3_path $prebuild_pip3_path install --trusted-host $trusted_host -i $pypi_url idna\>\=3.7 urllib3\>\=1.26.29 pyyaml requests\>\=2.32.1 prompt_toolkit\=\=1.0.14 asn1crypto cryptography json5\=\=0.9.6
if [[ "$DOWNLOAD_SDK" == "YES" ]] && [[ ! -d "${code_dir}/prebuilts/ohos-sdk-12" && ! -d "${code_dir}/prebuilts/ohos-sdk/12" ]]; then
  $prebuild_python3_path ${code_dir}/build/scripts/download_sdk.py --branch OpenHarmony-5.0.0-Release --product-name ohos-sdk-full-5.0.0 --api-version 12
  mkdir -p ${code_dir}/prebuilts/ohos-sdk-12
  mv ${code_dir}/prebuilts/ohos-sdk ${code_dir}/prebuilts/ohos-sdk-12
fi

# llvm_ndk is merged form llvm and libcxx-ndk for compiling the native of hap
if [[ "${host_platform}" == "linux" ]]; then
    llvm_dir="${code_dir}/prebuilts/clang/ohos/linux-aarch64"
else
    llvm_dir="${code_dir}/prebuilts/clang/ohos/linux-x86_64"
fi
llvm_dir_win="${code_dir}/prebuilts/clang/ohos/windows-x86_64"
llvm_dir_mac_x86="${code_dir}/prebuilts/clang/ohos/darwin-x86_64"
llvm_dir_mac_arm64="${code_dir}/prebuilts/clang/ohos/darwin-arm64"
llvm_dir_ohos_arm64="${code_dir}/prebuilts/clang/ohos/ohos-arm64"
llvm_dir_list=($llvm_dir $llvm_dir_win $llvm_dir_mac_x86 $llvm_dir_mac_arm64 $llvm_dir_ohos_arm64)

# copy libcxx-ndk library outside c++
function copy_inside_cxx(){
for i in ${llvm_dir_list[@]}
do
    libcxx_dir="${i}/libcxx-ndk/lib"
    if [[ -d "${i}/libcxx-ndk" ]]; then
        for file in $(ls ${libcxx_dir})
        do
            if [ ! -d "${libcxx_dir}/${file}/c++" ];then
                $(mkdir -p ${libcxx_dir}/c++)
                $(cp -r ${libcxx_dir}/${file}/* ${libcxx_dir}/c++)
                $(mv ${libcxx_dir}/c++ ${libcxx_dir}/${file}/c++)
            fi
        done
    fi
done
}

function update_llvm_ndk(){
if [[ -e "${llvm_dir}/llvm_ndk" ]];then
  rm -rf "${llvm_dir}/llvm_ndk"
fi
mkdir -p "${llvm_dir}/llvm_ndk"
cp -af "${llvm_dir}/llvm/include" "${llvm_dir}/llvm_ndk"
cp -rfp "${llvm_dir}/libcxx-ndk/include" "${llvm_dir}/llvm_ndk"
}

if [[ "${BUILD_ARKUIX}" != "YES" ]]; then
    copy_inside_cxx
    echo "======copy inside cxx finished!======"
    if [[ "${host_platform}" == "linux" ]]; then
        update_llvm_ndk
        echo "======update llvm ndk finished!======"
    fi
fi
echo -e "\n"
fi
