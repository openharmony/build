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
  case $i in 
    -skip-ssl|--skip-ssl) # wget、npm跳过ssl检查,如使用此参数:
    # 黑客等不法分子可以篡改或窃取客户端和服务器之间传输的信息和数据，从而影响用户的数据安全!
    SKIP_SSL=YES
    ;;
  esac
done
if [ "X${SKIP_SSL}" == "XYES" ];then
    wget_ssl_check='--no-check-certificate'
else
    wget_ssl_check=
fi
sha256_result=0
check_sha256=
local_sha256=
function check_sha256(){
    success_color='\033[1;42mSuccess\033[0m'
    failed_color='\033[1;41mFailed\033[0m'
    check_url=$1 #来源URL
    local_file=$2  #本地文件绝对路径
    check_sha256=`curl -s -k ${check_url}.sha256`  # 当前使用华为云,URL固定,所以写死了,后续如果有变动,此处需要修改
    local_sha256=`sha256sum ${local_file} |awk '{print $1}'`
    if [ "X${check_sha256}" == "X${local_sha256}" ];then
        echo -e "${success_color},${check_url} Sha256 check OK."
        sha256_result=0
    else
        echo -e "${failed_color},${check_url} Sha256 check Failed.Retry!"
        sha256_result=1
        #exit 1  # 默认退出,必须保证sha256一致,如有特殊需要,请自行注释
    fi
}
function hwcloud_download(){
    # 代理不需要鉴权: wget -O ${bin_dir} -e "https_proxy=http://domain.com:port" ${huaweicloud_url}
    # 代理需要鉴权(账号密码特殊字符均需要URL转义): wget -O ${bin_dir} -e "https_proxy=http://username:password@domain.com:port" ${huaweicloud_url}
    # 不需要代理
    download_local_file=$1
    download_source_url=$2
    for((i=1;i<=3;i++));
    do
        if [ -f "${download_local_file}" ];then
            check_sha256 "${download_source_url}" "${download_local_file}"
            if [ ${sha256_result} -gt 0 ];then
                # 设置变量默认值,防止误删除
                rm -rf "${download_local_file:-/tmp/20210721_not_exit_file}"
            else
                i=999
                return 0
            fi
        fi
        if [ ! -f "${download_local_file}" ];then
            wget ${wget_ssl_check} -O  "${download_local_file}" "${download_source_url}"
        fi
    done
    # 连续三次失败后报错退出
    echo -e """Sha256 check failed!
Download URL: ${download_source_url}
Local file: ${download_local_file}
Remote sha256: ${check_sha256}
Local sha256: ${local_sha256}"""
    exit 1
}
# 代码下载目录
script_path=$(cd $(dirname $0);pwd)
code_dir=$(dirname ${script_path})
# 二进制所在目录,用于临时存放二进制,需要约7G空间
# 下载的压缩包会自动解压到代码目录，压缩包会一直保留在该目录下
bin_dir=${code_dir}/../OpenHarmony_2.0_canary_prebuilts

# 二进制关系
copy_config="""prebuilts/cmake,https://repo.huaweicloud.com/harmonyos/compiler/cmake/3.16.5/darwin/cmake-darwin-x86-3.16.5.tar.gz
prebuilts/cmake,https://repo.huaweicloud.com/harmonyos/compiler/cmake/3.16.5/linux/cmake-linux-x86-3.16.5.tar.gz
prebuilts/cmake,https://repo.huaweicloud.com/harmonyos/compiler/cmake/3.16.5/windows/cmake-windows-x86-3.16.5.tar.gz
prebuilts/build-tools/darwin-x86/bin,https://repo.huaweicloud.com/harmonyos/compiler/gn/1717/darwin/gn-darwin-x86-1717.tar.gz
prebuilts/build-tools/linux-x86/bin,https://repo.huaweicloud.com/harmonyos/compiler/gn/1717/linux/gn-linux-x86-1717.tar.gz
prebuilts/build-tools/darwin-x86/bin,https://repo.huaweicloud.com/harmonyos/compiler/ninja/1.10.1/darwin/ninja-darwin-x86-1.10.1.tar.gz
prebuilts/build-tools/linux-x86/bin,https://repo.huaweicloud.com/harmonyos/compiler/ninja/1.10.1/linux/ninja-linux-x86-1.10.1.tar.gz
prebuilts/python,https://repo.huaweicloud.com/harmonyos/compiler/python/3.8.5/darwin/python-darwin-x86-3.8.5.tar.gz
prebuilts/python,https://repo.huaweicloud.com/harmonyos/compiler/python/3.8.5/linux/python-linux-x86-3.8.5.tar.gz
prebuilts/mingw-w64/ohos/linux-x86_64,https://repo.huaweicloud.com/harmonyos/compiler/mingw-w64/7.0.0/clang-mingw.tar.gz
prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi,https://repo.huaweicloud.com/harmonyos/compiler/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi/1.0/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi.tar.gz
prebuilts/gcc/linux-x86/aarch64,https://repo.huaweicloud.com/harmonyos/compiler/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi/1.0/gcc-linaro-7.5.0-2019.12-x86_64_aarch64-linux-gnu.tar.xz
prebuilts/sdk/js-loader/build-tools,https://repo.huaweicloud.com/harmonyos/compiler/ace-loader/1.0/ace-loader-1.0.tar.gz
prebuilts/clang/ohos/linux-x86_64,https://repo.huaweicloud.com/harmonyos/compiler/clang/10.0.1-69957/linux/clang-69957-linux-x86_64.tar.bz2
prebuilts/build-tools/common,https://repo.huaweicloud.com/harmonyos/compiler/restool/1.023-c/restool.tar.gz
"""
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
    if [ "X${bin_file_suffix:0-3}" = "Xzip" ];then
        unzip "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}" -d "${code_dir}/${unzip_dir}/"
    elif [ "X${bin_file_suffix:0-6}" = "Xtar.gz" ];then
        tar -xvzf "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}"  -C  "${code_dir}/${unzip_dir}"
    else
        tar -xvf "${bin_dir}/${md5_huaweicloud_url}.${bin_file_suffix}"  -C  "${code_dir}/${unzip_dir}"
    fi
    # 由于部分压缩包包含了目录,用于专门处理多余目录
    if [ -d "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi" ];then
        mv "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/prebuilts_gcc_linux-x86_arm_gcc-linaro-7.5.0-arm-linux-gnueabi" "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi2/"
        rm -rf "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi"
        mv "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi2/" "${code_dir}/prebuilts/gcc/linux-x86/arm/gcc-linaro-7.5.0-arm-linux-gnueabi/"
    fi
    if [ -d "${code_dir}/prebuilts/clang/ohos/linux-x86_64/clang-69957" ];then
        mv "${code_dir}/prebuilts/clang/ohos/linux-x86_64/clang-69957" "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm2"
        rm -rf "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm"
        mv "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm2" "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm"
	ln -snf 10.0.1 "${code_dir}/prebuilts/clang/ohos/linux-x86_64/llvm/lib/clang/current"
    fi
done


node_js_ver=v12.18.4
node_js=node-${node_js_ver}-linux-x64.tar.gz
mkdir -p ${code_dir}/prebuilts/build-tools/common/nodejs
cd ${code_dir}/prebuilts/build-tools/common/nodejs
if [ ! -f "${node_js}" ]; then
    wget ${wget_ssl_check} https://repo.huaweicloud.com/nodejs/${node_js_ver}/${node_js}
    tar zxf ${node_js}
fi

if [ ! -d "${code_dir}/third_party/jsframework" ]; then
    echo "${code_dir}/third_party/jsframework not exist, it shouldn't happen, pls check..."
else
    cd ${code_dir}/third_party/jsframework/
    export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/node-v12.18.4-linux-x64/bin:$PATH
    npm config set registry http://registry.npm.taobao.org
    if [ "X${SKIP_SSL}" == "XYES" ];then
        npm config set strict-ssl false
    fi
    npm install

    cd ${code_dir}
    if [ -d "${code_dir}/prebuilts/build-tools/common/js-framework" ]; then
        echo -e "\n"
        echo "${code_dir}/prebuilts/build-tools/common/js-framework already exist, it will be replaced with node-${node_js_ver}"
        /bin/rm -rf ${code_dir}/prebuilts/build-tools/common/js-framework
        echo -e "\n"
    fi

    mkdir -p ${code_dir}/prebuilts/build-tools/common/js-framework
    /bin/cp -rf ${code_dir}/third_party/jsframework/node_modules ${code_dir}/prebuilts/build-tools/common/js-framework/
fi

cd ${code_dir}
echo -e "\n"
