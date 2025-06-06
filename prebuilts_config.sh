#!/bin/bash
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
home_path=$HOME
config_file="$script_path/prebuilts_config.json"


# 处理命令行参数
declare -A args
parse_args(){
    while [[ $# -gt 0 ]]; do
        case "$1" in
            # 处理长参数（带等号）
            --*=*)
                key="${1%%=*}"     # 提取参数名
                value="${1#*=}"    # 提取参数值
                args["$key"]="$value"  # 取最后的值
                shift
                ;;
            # 处理长参数（不带等号）
            --*)
                key="$1"
                shift
                values=()
                # 收集所有连续的非选项参数作为值
                while [[ $# -gt 0 && "$1" != -* ]]; do
                    values+=("$1")
                    shift
                done
                if [[ ${#values[@]} -eq 0 ]]; then
                    args["$key"]="1"  # 无值参数标记为1
                else
                    args["$key"]="${values[*]}"  # 合并为空格分隔的字符串
                fi
                ;;
            # 处理短参数（带等号，如 -k=value）
            -*=*)
                key_part="${1%%=*}"    # 提取短参数部分（如 -abc=value → -abc）
                value="${1#*=}"       # 提取值
                chars="${key_part:1}" # 去掉前缀的短参数（如 abc）
                # 处理除最后一个字符外的所有字符（作为无值参数）
                while [[ ${#chars} -gt 1 ]]; do
                    args["-${chars:0:1}"]="1"
                    chars="${chars:1}"
                done
                # 最后一个字符作为带值参数
                args["-${chars}"]="$value"
                shift
                ;;
            # 处理短参数（不带等号）
            -*)
                chars="${1:1}"  # 去掉短参数前缀（如 abc）
                while [[ -n "$chars" ]]; do
                    key="-${chars:0:1}"
                    chars="${chars:1}"
                    # 如果还有剩余字符或后续参数是选项，视为无值参数
                    if [[ -n "$chars" ]] || [[ $# -gt 1 && "$2" == -* ]]; then
                        args["$key"]="1"
                    else
                        # 否则取下一个参数作为值
                        args["$key"]="$2"
                        shift
                    fi
                done
                shift
                ;;
            # 不处理其他参数
            *)
                shift
                ;;
        esac
    done

    for key in "${!args[@]}"; do
        # 去除值首位的空格（因追加逻辑可能产生）
        value="${args[$key]# }"
        args[$key]=$value
    done
}

parse_args "$@"

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

if [[ "${glibc_version}" < "2.35" ]]; then
    glibc_version="--glibc-version GLIBC2.27"
else
    glibc_version="--glibc-version GLIBC2.35"
fi

if [[ -v args["--pypi-url"] ]]; then
    pypi_url=${args["--pypi_url"]}
else
    pypi_url='http://repo.huaweicloud.com/repository/pypi/simple'
fi

if [[ -v args["--trusted_host"] ]]; then
    trusted_host=${args["--trusted_host"]}
elif [ ! -z "$pypi_url" ];then
    trusted_host=${pypi_url/#*:\/\//}       # remove prefix part such as http:// https:// etc.
    trusted_host=${trusted_host/%[:\/]*/}   # remove suffix part including the port number
else
    trusted_host='repo.huaweicloud.com'
fi


if [[ -v args["--disable-rich"] ]]; then
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

if [[ -v args["--part-names"] ]]; then
    part_names="--part-names ${args["--part-names"]}"
fi

# 运行Python命令
python3 "${script_path}/prebuilts_config.py" $glibc_version --config-file $config_file --host-platform $host_platform --host-cpu $host_cpu $disable_rich $part_names
PYTHON_PATH=$(realpath $code_dir/prebuilts/python/${host_platform}-${host_cpu_prefix}/*/bin | tail -1)

if [[ -v args["--download-sdk"] ]]; then
    DOWNLOAD_SDK=YES
fi

if [[ "$DOWNLOAD_SDK" == "YES" ]] && [[ ! -d "${code_dir}/prebuilts/ohos-sdk/linux" ]]; then
  $PYTHON_PATH/python3 ${code_dir}/build/scripts/download_sdk.py --branch master --product-name ohos-sdk-full-linux --api-version 20
fi



if [[ "${target_os}" == "linux" ]]; then
    sed -i "1s%.*%#!/usr/bin/env python3%" "${PYTHON_PATH}/pip3"
elif [[ "${target_os}" == "darwin" ]]; then
    sed -i "" "1s%.*%#!/usr/bin/env python3%" "${PYTHON_PATH}/pip3"
fi

# llvm_ndk is merged form llvm and libcxx-ndk for compiling the native of hap
llvm_dir="${code_dir}/prebuilts/clang/ohos/linux-x86_64"
llvm_dir_win="${code_dir}/prebuilts/clang/ohos/windows-x86_64"
llvm_dir_mac_x86="${code_dir}/prebuilts/clang/ohos/darwin-x86_64"
llvm_dir_mac_arm64="${code_dir}/prebuilts/clang/ohos/darwin-arm64"
llvm_dir_list=($llvm_dir $llvm_dir_win $llvm_dir_mac_x86 $llvm_dir_mac_arm64)

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

function change_rustlib_name(){
rust_dir="${code_dir}/prebuilts/rustc/linux-x86_64/current/lib/rustlib/"
for file in $(find "$rust_dir" -path "$rust_dir/x86_64-unknown-linux-gnu" -prune -o -name "lib*.*")
do
    dir_name=${file%/*}
    file_name=${file##*/}
    file_prefix=$(echo "$file_name" | awk '{split($1, arr, "."); print arr[1]}')
    file_prefix=$(echo "$file_prefix" | awk '{split($1, arr, "-"); print arr[1]}')
    file_suffix=$(echo "$file_name" | awk '{split($1, arr, "."); print arr[2]}')
    if [[ "$file_suffix" != "rlib" && "$file_suffix" != "so" || "$file_prefix" == "librustc_demangle" || "$file_prefix" == "libcfg_if" || "$file_prefix" == "libunwind" ]]
    then
        continue
    fi
    if [[ "$file_suffix" == "rlib" ]]
    then
        if [[ "$file_prefix" == "libstd" || "$file_prefix" == "libtest" ]]
        then
            newfile_name="$file_prefix.dylib.rlib"
        else
            newfile_name="$file_prefix.rlib"
        fi
    fi

    if [[ "$file_suffix" == "so" ]]
    then
        newfile_name="$file_prefix.dylib.so"
    fi
    if [[ "$file_name" == "$newfile_name" ]]
    then
        continue
    fi
    mv $file "$dir_name/$newfile_name"
done
}
copy_inside_cxx
echo "======copy inside cxx finished!======"
echo -e "\033[0;33myou can use --skip-prebuilts to skip prebuilts_download step while using hb build command\033[0m"
