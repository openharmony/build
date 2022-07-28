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

cpu="--host-cpu $host_cpu"
platform="--host-platform $host_platform"
trusted_host='repo.huaweicloud.com'
index_url='http://repo.huaweicloud.com/repository/pypi/simple'

script_path=$(cd $(dirname $0);pwd)
code_dir=$(dirname ${script_path})
pip3 install --trusted-host $trusted_host -i $index_url rich
echo "prebuilts_download start"
python3 "${code_dir}/build/prebuilts_download.py" $wget_ssl_check $tool_repo $npm_registry $help $cpu $platform
echo "prebuilts_download end"


if [[ "${host_platform}" == "linux" ]]; then
    sed -i "1s%.*%#!$code_dir/prebuilts/python/${host_platform}-x86/3.9.2/bin/python3.9%" ${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9
elif [[ "${host_platform}" == "darwin" ]]; then
    sed -i "" "1s%.*%#!$code_dir/prebuilts/python/${host_platform}-x86/3.9.2/bin/python3.9%" ${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9
fi
${code_dir}/prebuilts/python/${host_platform}-x86/3.9.2/bin/pip3.9 install --trusted-host $trusted_host -i $index_url pyyaml requests prompt_toolkit\=\=1.0.14 kconfiglib\>\=14.1.0
echo -e "\n"
