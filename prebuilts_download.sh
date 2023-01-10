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
    *)
    echo "$0: Warning: unsupported parameter: $1" >&2
    ;;
  esac
  shift
done

case $(uname -s) in
    Linux)

        host_platform=linux
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
        ;;
    *)
        host_cpu=x86_64
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
script_path=$(cd $(dirname $0);pwd)
code_dir=$(dirname ${script_path})
echo "prebuilts_download start"
python3 "${code_dir}/build/prebuilts_download.py" $wget_ssl_check $tool_repo $npm_registry $help $cpu $platform $npm_para $disable_rich $enable_symlink
echo "prebuilts_download end"

# llvm_ndk is merged form llvm and libcxx-ndk for compiling the native of hap
llvm_dir="${code_dir}/prebuilts/clang/ohos/linux-x86_64"
if [[ -e "${llvm_dir}/llvm_ndk" ]];then
  rm -rf "${llvm_dir}/llvm_ndk"
fi
mkdir -p "${llvm_dir}/llvm_ndk"
cp -af "${llvm_dir}/llvm/include" "${llvm_dir}/llvm_ndk"
cp -rfp "${llvm_dir}/libcxx-ndk/include/libcxx-ohos/include" "${llvm_dir}/llvm_ndk"

if [[ "${host_platform}" == "linux" ]]; then
    sed -i "1s%.*%#!/usr/bin/env python3%" ${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9
elif [[ "${host_platform}" == "darwin" ]]; then
    sed -i "" "1s%.*%#!/use/bin/env python3%" ${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9
fi
prebuild_python3_path="$code_dir/prebuilts/python/${host_platform}-x86/3.9.2/bin/python3.9"
prebuild_pip3_path="${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9"
$prebuild_python3_path $prebuild_pip3_path install --trusted-host $trusted_host -i $pypi_url pyyaml requests prompt_toolkit\=\=1.0.14 kconfiglib\>\=14.1.0
echo -e "\n"
