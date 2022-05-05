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
for i in "$@"; do
  case "$i" in
    -skip-ssl|--skip-ssl) # wget、npm skip ssl check, which will allow
                          # hacker to get and modify data stream between server and client!
    SKIP_SSL=YES
    ;;
  esac
done

if [ "X${SKIP_SSL}" == "XYES" ];then
    wget_ssl_check='--no-check-certificate'
else
    wget_ssl_check=''
fi

if [ -z "$TOOL_REPO" ];then
	tool_repo='https://repo.huaweicloud.com'
else
	tool_repo=$TOOL_REPO
fi
echo "tool_repo=$tool_repo"

if [ -z "$NPM_REGISTRY" ];then
	npm_registry='http://registry.npm.taobao.org'
else
	npm_registry=$NPM_REGISTRY
fi
echo "npm_registry=$npm_registry"

sha256_result=0
check_sha256=''
local_sha256=''

function check_sha256() {
    success_color='\033[1;42mSuccess\033[0m'
    failed_color='\033[1;41mFailed\033[0m'
    check_url=$1 # source URL
    local_file=$2  # local absolute path
    check_sha256=$(curl -s -k ${check_url}.sha256)
    local_sha256=$(sha256sum ${local_file} |awk '{print $1}')
    if [ "X${check_sha256}" == "X${local_sha256}" ];then
        echo -e "${success_color},${check_url} Sha256 check OK."
        sha256_result=0
    else
        echo -e "${failed_color},${check_url} Sha256 check Failed.Retry!"
        sha256_result=1
    fi
}

function hwcloud_download() {
    # when proxy certfication not required : wget -t3 -T10 -O ${bin_dir} -e "https_proxy=http://domain.com:port" ${huaweicloud_url}
    # when proxy certfication required (special char need URL translate, e.g '!' -> '%21'git
    # wget -t3 -T10 -O ${bin_dir} -e "https_proxy=http://username:password@domain.com:port" ${huaweicloud_url}

    download_local_file=$1
    download_source_url=$2
    for((i=1;i<=3;i++));
    do
        if [ -f "${download_local_file}" ];then
            check_sha256 "${download_source_url}" "${download_local_file}"
            if [ ${sha256_result} -gt 0 ];then
                rm -rf "${download_local_file:-/tmp/20210721_not_exit_file}"
            else
                return 0
            fi
        fi
        if [ ! -f "${download_local_file}" ];then
            wget -t3 -T10 ${wget_ssl_check} -O  "${download_local_file}" "${download_source_url}"
        fi
    done
    # three times error, exit
    echo -e """Sha256 check failed!
Download URL: ${download_source_url}
Local file: ${download_local_file}
Remote sha256: ${check_sha256}
Local sha256: ${local_sha256}"""
    exit 1
}

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

# sync code directory
script_path=$(cd $(dirname $0);pwd)
code_dir=$(dirname ${script_path})
# "prebuilts" directory will be generated under project root which is used to saved binary (arround 9.5GB)
# downloaded files will be automatically unziped under this path
bin_dir=${code_dir}/../OpenHarmony_2.0_canary_prebuilts

# download file list
copy_config="""
prebuilts/sdk/js-loader/build-tools,${tool_repo}/harmonyos/compiler/ace-loader/1.0/ace-loader-1.0.tar.gz
prebuilts/build-tools/common,${tool_repo}/harmonyos/compiler/restool/2.007/restool-2.007.tar.gz
prebuilts/cmake,${tool_repo}/harmonyos/compiler/cmake/3.16.5/${host_platform}/cmake-${host_platform}-x86-3.16.5.tar.gz
prebuilts/build-tools/${host_platform}-x86/bin,${tool_repo}/harmonyos/compiler/gn/1717/${host_platform}/gn-${host_platform}-x86-1717.tar.gz
prebuilts/build-tools/${host_platform}-x86/bin,${tool_repo}/harmonyos/compiler/ninja/1.10.1/${host_platform}/ninja-${host_platform}-x86-1.10.1.tar.gz
prebuilts/python,${tool_repo}/harmonyos/compiler/python/3.8.5/${host_platform}/python-${host_platform}-x86-3.8.5.tar.gz
prebuilts/clang/ohos/${host_platform}-x86_64,${tool_repo}/harmonyos/compiler/clang/10.0.1-480513/${host_platform}/clang-480513-${host_platform}-x86_64.tar.bz2
prebuilts/ark_tools,${tool_repo}/harmonyos/compiler/llvm_prebuilt_libs/ark_js_prebuilts_20220425.tar.gz
"""

if [[ "${host_platform}" == "linux" ]]; then
    copy_config+="""
        prebuilts/cmake,${tool_repo}/harmonyos/compiler/cmake/3.16.5/windows/cmake-windows-x86-3.16.5.tar.gz
        prebuilts/mingw-w64/ohos/linux-x86_64,${tool_repo}/harmonyos/compiler/mingw-w64/7.0.0/clang-mingw.tar.gz
        prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi,${tool_repo}/harmonyos/compiler/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi/1.0/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi.tar.gz
        prebuilts/gcc/linux-x86/aarch64,${tool_repo}/harmonyos/compiler/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi/1.0/gcc-linaro-7.5.0-2019.12-x86_64_aarch64-linux-gnu.tar.xz
        prebuilts/previewer/windows,${tool_repo}/harmonyos/develop_tools/previewer/3.1.5.4/previewer-3.1.5.4.win.tar.gz
        prebuilts/clang/ohos/windows-x86_64,${tool_repo}/harmonyos/compiler/clang/10.0.1-480513/windows/clang-480513-windows-x86_64.tar.bz2
        prebuilts/clang/ohos/windows-x86_64,${tool_repo}/harmonyos/compiler/clang/10.0.1-480513/windows/libcxx-ndk-480513-windows-x86_64.tar.bz2
        prebuilts/clang/ohos/${host_platform}-x86_64,${tool_repo}/harmonyos/compiler/clang/10.0.1-480513/${host_platform}/libcxx-ndk-480513-${host_platform}-x86_64.tar.bz2
        prebuilts/gcc/linux-x86/esp,${tool_repo}/harmonyos/compiler/gcc_esp/2019r2-8.2.0/linux/esp-2019r2-8.2.0.zip
        prebuilts/gcc/linux-x86/csky,${tool_repo}/harmonyos/compiler/gcc_csky/v3.10.29/linux/csky-v3.10.29.tar.gz
        """
elif [[ "${host_platform}" == "darwin" ]]; then
    copy_config+="""
        prebuilts/previewer/darwin,${tool_repo}/harmonyos/develop_tools/previewer/3.1.5.4/previewer-3.1.5.4.mac.tar.gz
        prebuilts/clang/ohos/${host_platform}-x86_64,${tool_repo}/harmonyos/compiler/clang/10.0.1-480513/${host_platform}/libcxx-ndk-480513-${host_platform}-x86_64.tar.bz2
        """
fi

if [ ! -d "${bin_dir}" ];then
    mkdir -p "${bin_dir}"
fi

for i in $(echo ${copy_config})
do
    unzip_dir=$(echo $i|awk -F ',' '{print $1}')
    huaweicloud_url=$(echo $i|awk -F ',' '{print $2}')
    md5_huaweicloud_url=$(echo ${huaweicloud_url}|md5sum|awk '{print $1}')
    bin_file=$(basename ${huaweicloud_url})
    bin_file_suffix=${bin_file#*.}
    #huaweicloud_file_name=$(echo ${huaweicloud_url}|awk -F '/' '{print $NF}')

    if [ ! -d "${code_dir}/${unzip_dir}" ];then
        mkdir -p "${code_dir}/${unzip_dir}"
    fi
    hwcloud_download "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}"  "${huaweicloud_url}"

    if [ ! -f "${code_dir}/${unzip_dir}/${check_sha256}.mark" ]; then
        if [ "X${bin_file_suffix:0-3}" = "Xzip" ];then
            unzip -o "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}" -d "${code_dir}/${unzip_dir}/"
        elif [ "X${bin_file_suffix:0-6}" = "Xtar.gz" ];then
            tar -xvzf "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}"  -C  "${code_dir}/${unzip_dir}"
        else
            tar -xvf "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}"  -C  "${code_dir}/${unzip_dir}"
        fi
        echo 0 > "${code_dir}/${unzip_dir}/${check_sha256}.mark"
    fi

    # it is used to handle some redundant files under prebuilts path
    if [ -d "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi" ];then
        mv "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi" "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi2/"
        rm -rf "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi"
        mv "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi2/" "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/"
    fi
    if [ -d "${code_dir}/prebuilts/clang/ohos/windows-x86_64/clang-480513" ];then
        rm -rf "${code_dir}/prebuilts/clang/ohos/windows-x86_64/llvm"
        mv "${code_dir}/prebuilts/clang/ohos/windows-x86_64/clang-480513" "${code_dir}/prebuilts/clang/ohos/windows-x86_64/llvm"
    ln -snf 10.0.1 "${code_dir}/prebuilts/clang/ohos/windows-x86_64/llvm/lib/clang/current"
    fi
    if [ -d "${code_dir}/prebuilts/clang/ohos/linux-x86_64/clang-480513" ];then
        rm -rf "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm"
        mv "${code_dir}/prebuilts/clang/ohos/linux-x86_64/clang-480513" "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm"
	ln -snf 10.0.1 "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm/lib/clang/current"
    fi
    if [ -d "${code_dir}/prebuilts/clang/ohos/darwin-x86_64/clang-480513" ];then
        rm -rf "${code_dir}/prebuilts/clang/ohos/darwin-x86_64/llvm"
        mv "${code_dir}/prebuilts/clang/ohos/darwin-x86_64/clang-480513" "${code_dir}/prebuilts/clang/ohos/darwin-x86_64/llvm"
	ln -snf 10.0.1 "${code_dir}/prebuilts/clang/ohos/darwin-x86_64/llvm/lib/clang/current"
    fi
    if [ -d "${code_dir}/prebuilts/gcc/linux-x86/esp/esp-2019r2-8.2.0/xtensa-esp32-elf" ];then
        chmod 755 "${code_dir}/prebuilts/gcc/linux-x86/esp/esp-2019r2-8.2.0" -R
    fi
done


node_js_ver=v12.18.4
node_js_name=node-${node_js_ver}-${host_platform}-x64
node_js_pkg=${node_js_name}.tar.gz
mkdir -p ${code_dir}/prebuilts/build-tools/common/nodejs
cd ${code_dir}/prebuilts/build-tools/common/nodejs
if [ ! -f "${node_js_pkg}" ]; then
    wget -t3 -T10 ${wget_ssl_check} ${tool_repo}/nodejs/${node_js_ver}/${node_js_pkg}
    tar zxf ${node_js_pkg}
fi

if [ ! -d "${code_dir}/third_party/jsframework" ]; then
    echo "${code_dir}/third_party/jsframework not exist, it shouldn't happen, pls check..."
else
    cd ${code_dir}/third_party/jsframework/
    export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/${node_js_name}/bin:$PATH
    npm config set registry ${npm_registry}
    if [ "X${SKIP_SSL}" == "XYES" ];then
        npm config set strict-ssl false
    fi
    npm cache clean -f
    npm install

    cd ${code_dir}
    if [ -d "${code_dir}/prebuilts/build-tools/common/js-framework" ]; then
        echo -e "\n"
        echo "${code_dir}/prebuilts/build-tools/common/js-framework already exist, it will be replaced with node-${node_js_ver}"
        /bin/rm -rf ${code_dir}/prebuilts/build-tools/common/js-framework
        echo -e "\n"
    fi

    mkdir -p ${code_dir}/prebuilts/build-tools/common/js-framework
    /bin/cp -R ${code_dir}/third_party/jsframework/node_modules ${code_dir}/prebuilts/build-tools/common/js-framework/
fi

if [ ! -d "${code_dir}/developtools/ace-ets2bundle/compiler" ]; then
    echo "${code_dir}/developtools/ace-ets2bundle/compiler not exist, it shouldn't happen, pls check..."
else
    cd ${code_dir}/developtools/ace-ets2bundle/compiler
    export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/${node_js_name}/bin:$PATH
    npm config set registry ${npm_registry}
    if [ "X${SKIP_SSL}" == "XYES" ];then
        npm config set strict-ssl false
    fi
    npm cache clean -f
    npm install
fi


if [ ! -d "${code_dir}/developtools/ace-js2bundle/ace-loader" ]; then
    echo "${code_dir}/developtools/ace-js2bundle/ace-loader not exist, it shouldn't happen, pls check..."
else
    cd ${code_dir}/developtools/ace-js2bundle/ace-loader
    export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/${node_js_name}/bin:$PATH
    npm config set registry ${npm_registry}
    if [ "X${SKIP_SSL}" == "XYES" ];then
        npm config set strict-ssl false
    fi
    npm cache clean -f
    npm install
fi


if [ -d "${code_dir}/ark/ts2abc/ts2panda" ]; then
    cd ${code_dir}/ark/ts2abc/ts2panda
    export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/${node_js_name}/bin:$PATH
    npm config set registry ${npm_registry}
    if [ "X${SKIP_SSL}" == "XYES" ];then
        npm config set strict-ssl false
    fi
    npm cache clean -f
    npm install

    cd ${code_dir}
    if [ -d "${code_dir}/prebuilts/build-tools/common/ts2abc" ]; then
        echo -e "\n"
        echo "${code_dir}/prebuilts/build-tools/common/ts2abc already exist, it will be replaced with node-${node_js_ver}"
        /bin/rm -rf ${code_dir}/prebuilts/build-tools/common/ts2abc
        echo -e "\n"
    fi

    mkdir -p ${code_dir}/prebuilts/build-tools/common/ts2abc
    /bin/cp -rf ${code_dir}/ark/ts2abc/ts2panda/node_modules ${code_dir}/prebuilts/build-tools/common/ts2abc/
fi


cd ${code_dir}
echo -e "\n"
