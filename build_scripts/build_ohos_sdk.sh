#!/bin/bash
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

function prebuilt_sdk() {
    local source_root_dir="$1"
    local python_dir="$2"
    local current_platform="$3"
    local ccache_args="$4"
    local xcache_args="$5"
    local api_version="$6"
    local generate_sbom="$7"
    shift 7
    local _sdk_gn_args=("$@")

    local ROOT_PATH="${source_root_dir}"
    local SDK_PREBUILTS_PATH="${ROOT_PATH}/prebuilts/ohos-sdk"
    local SDK_BUILD_REQUIRED=false

    
    pushd "${ROOT_PATH}" > /dev/null || {
        echo -e "\033[31m[OHOS ERROR] Failed to enter directory: ${ROOT_PATH}\033[0m"
        exit 1
    }
        echo -e "[OHOS INFO] Building the latest ohos-sdk..."
        ./build.py --product-name ohos-sdk \
            --python-dir ${python_dir} \
            ${ccache_args} \
            ${xcache_args} \
            --load-test-config=false \
            --get-warning-list=false \
            --stat-ccache=false \
            --compute-overlap-rate=false \
            --deps-guard=false \
            --generate-ninja-trace=false \
            --generate-sbom=${generate_sbom} \
            --gn-args "skip_generate_module_list_file=true sdk_platform=${current_platform} ndk_platform=${current_platform} use_cfi=false use_thin_lto=false enable_lto_O0=true sdk_check_flag=false enable_ndk_doxygen=false archive_ndk=false sdk_for_hap_build=true enable_archive_sdk=false enable_notice_collection=false enable_process_notice=false ${_sdk_gn_args[*]}"
        if [[ "$?" -ne 0 ]]; then
            echo -e "\033[31m[OHOS ERROR] ohos-sdk build failed! Try using '--no-prebuilts-sdk' to skip.\033[0m"
            exit 1
        fi
        [[ -d "${ROOT_PATH}/prebuilts/ohos-sdk/linux" ]] && rm -rf "${ROOT_PATH}/prebuilts/ohos-sdk/linux"
        mkdir -p "${SDK_PREBUILTS_PATH}"
        mv "${ROOT_PATH}/out/sdk/ohos-sdk/linux" "${SDK_PREBUILTS_PATH}/"
        mkdir -p "${SDK_PREBUILTS_PATH}/linux/native"
        mv "${ROOT_PATH}/out/sdk/sdk-native/os-irrelevant/"* "${SDK_PREBUILTS_PATH}/linux/native/"
        mv "${ROOT_PATH}/out/sdk/sdk-native/os-specific/linux/"* "${SDK_PREBUILTS_PATH}/linux/native/"
        pushd "${SDK_PREBUILTS_PATH}/linux" > /dev/null
            mkdir -p "${api_version}"
            for dir in */; do
                [[ -d "${dir}" && "${dir}" != "${api_version}/" ]] && mv "${dir}" "${api_version}/"
            done
        popd > /dev/null
    popd > /dev/null
    local target_dir="${source_root_dir}/prebuilts/ohos-sdk/linux/${api_version}/previewer"
    [[ ! -d "${target_dir}" ]] && mkdir -p "${target_dir}"
    cp -r "${source_root_dir}/prebuilts/ohos-sdk/linux/${api_version}/native/oh-uni-package.json" "${target_dir}/" 2>/dev/null
    sed -i 's/Native/Previewer/g' "${target_dir}/oh-uni-package.json" 2>/dev/null
    sed -i 's/native/previewer/g' "${target_dir}/oh-uni-package.json" 2>/dev/null
    if [[ -d "${source_root_dir}/prebuilts/ohos-sdk-12/ohos-sdk/linux/12" ]]; then
        mkdir -p "${source_root_dir}/prebuilts/ohos-sdk/linux/12"
        mv "${source_root_dir}/prebuilts/ohos-sdk-12/ohos-sdk/linux/12/"* "${source_root_dir}/prebuilts/ohos-sdk/linux/12/"
    fi
    if [[ "$?" -ne 0 ]]; then
        echo -e "\033[31m[OHOS ERROR] ohos-sdk post-processing failed!\033[0m"
        exit 1
    fi
    
}

function main() {
    if [[ $# -lt 6 ]]; then
        echo "Usage: $0 <source_root_dir> <ccache_args> <xcache_args> <api_version> <api_version> [prebuilt_sdk_gn_args...]"
        exit 1
    fi

    local source_root_dir="$1"
    local python_dir="$2"
    local current_platform="$3"
    local ccache_args="$4"
    local xcache_args="$5"
    local api_version="$6"
    shift 6

    local _sdk_gn_args=("$@")

    prebuilt_sdk \
        "${source_root_dir}" \
        "${python_dir}" \
        "${current_platform}" \
        "${ccache_args}" \
        "${xcache_args}" \
        "${api_version}" \
        "${_sdk_gn_args[@]}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi