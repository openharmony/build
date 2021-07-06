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

while test $# -gt 0; do
    case "$1" in
    --device-name)
        shift
        device_name="$1"
        ;;
    --ohos-build-out-dir)
        shift
        ohos_build_out_dir="$1"
        ;;
    -* | *)
        echo "Unrecognized option: $1"
        exit 1
        ;;
    esac
    shift
done

if [[ "${device_name}x" == "x" ]]; then
    echo "Error: the device_name cannot be empty."
    exit 1
fi


function build_vendro_image() {
    cp -arf prebuilts/aosp_prebuilt_libs/minisys/vendor ${ohos_build_out_dir}/images/
    if [[ -d "${ohos_build_out_dir}/vendor" ]]; then
        cp -arf ${ohos_build_out_dir}/vendor/* ${ohos_build_out_dir}/images/vendor/
    fi
    # remove img
    rm -rf ${ohos_build_out_dir}/images/vendor.img
    # build system image
    PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
        ${ohos_build_out_dir}/images/vendor \
        prebuilts/aosp_prebuilt_libs/minisys/vendor_image_info.txt \
        ${ohos_build_out_dir}/images/vendor.img \
        ${ohos_build_out_dir}/images/system
    if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
        echo "\033[31m  build: build vendor image error.\033[0m"
        exit 1
    fi
    echo -e "\033[32m  build vendor image successful.\033[0m"
}


function _update_build_prop() {
    local system_build_prop_file=${ohos_build_out_dir}/images/system/build.prop
    local ohos_build_prop_file=${OHOS_ROOT_PATH}/build/ohos_system.prop
    if [[ -f "${ohos_build_prop_file}" ]] && [[ -f "${system_build_prop_file}" ]]; then
        echo '' >> ${system_build_prop_file}
        cat ${ohos_build_prop_file} >> ${system_build_prop_file}
    fi
}

function build_system_images_for_musl() {
    cp ${ohos_build_out_dir}/../../common/common/sh  ${ohos_build_out_dir}/images/system/bin/sh
    cp ${ohos_build_out_dir}/../../common/common/toybox  ${ohos_build_out_dir}/images/system/bin/toybox
    toybox_creater=${OHOS_ROOT_PATH}/build/adapter/images/create_init_toybox.sh
    ${toybox_creater} ${ohos_build_out_dir}/images/system/bin
}

function copy_init() {
    cp ${ohos_build_out_dir}/system/etc/init.Hi3516DV300.cfg ${ohos_build_out_dir}/images/root/init.Hi3516DV300.cfg
    cp ${ohos_build_out_dir}/system/etc/init.cfg ${ohos_build_out_dir}/images/root/init.cfg
    # It will be deleted after the musl compilation is completely successful
    if [[ $USE_OHOS_INIT != true ]]; then
        cp ${OHOS_ROOT_PATH}/prebuilts/aosp_prebuilt_libs/minisys/system/bin/init ${ohos_build_out_dir}/images/system/bin/init
        cp ${OHOS_ROOT_PATH}/prebuilts/aosp_prebuilt_libs/minisys/system/bin/reboot ${ohos_build_out_dir}/images/system/bin/reboot
        cp ${OHOS_ROOT_PATH}/prebuilts/aosp_prebuilt_libs/minisys/system/bin/sh ${ohos_build_out_dir}/images/system/bin/sh
        cp ${OHOS_ROOT_PATH}/prebuilts/aosp_prebuilt_libs/minisys/system/bin/toybox ${ohos_build_out_dir}/images/system/bin/toybox
    fi
}

function build_system_image() {
    if [[ ! -d "${ohos_build_out_dir}/images" ]]; then
        mkdir ${ohos_build_out_dir}/images
    fi
    cp -arf prebuilts/aosp_prebuilt_libs/minisys/system ${ohos_build_out_dir}/images/
    cp -arf ${ohos_build_out_dir}/system/* ${ohos_build_out_dir}/images/system/
    # update build.prop
    _update_build_prop
    # build for init
    copy_init
    if [[ $BUILD_WITH_MUSL == true ]]; then
        build_system_images_for_musl
    fi
    # remove img
    rm -rf ${ohos_build_out_dir}/images/system.img
    # build system image
    PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
        ${ohos_build_out_dir}/images/system \
        prebuilts/aosp_prebuilt_libs/minisys/system_image_info.txt \
        ${ohos_build_out_dir}/images/system.img \
        ${ohos_build_out_dir}/images/system
    if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
        echo "\033[31m  build: build system image error.\033[0m"
        exit 1
    fi
    echo -e "\033[32m  build system image successful.\033[0m"
}

function build_userdata_image() {
    if [[ -d "${ohos_build_out_dir}/images/data" ]]; then
        rm -rf ${ohos_build_out_dir}/images/data
    fi
    mkdir ${ohos_build_out_dir}/images/data
    # build userdat image
    PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
        ${ohos_build_out_dir}/images/data \
        prebuilts/aosp_prebuilt_libs/minisys/userdata_image_info.txt \
        ${ohos_build_out_dir}/images/userdata.img \
        ${ohos_build_out_dir}/images/system
    if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
        echo "\033[31m  build: build userdata image error.\033[0m"
        exit 1
    fi
    echo -e "\033[32m  build userdata image successful.\033[0m"
}


function prepare_root() {
    if [[ -d "${ohos_build_out_dir}/images/root" ]]; then
        rm -rf ${ohos_build_out_dir}/images/root
    fi
    cp -arf prebuilts/aosp_prebuilt_libs/minisys/root ${ohos_build_out_dir}/images/

    local dir_list=(acct apex cache config data debug_ramdisk dev mnt oem proc sbin storage sys system vendor)
    pushd ${ohos_build_out_dir}/images/root
    for _path in ${dir_list[@]}
    do
        if [[ ! -d "${_path}" ]]; then
            mkdir ${_path}
        fi
    done
    popd
}

prepare_root
build_vendro_image
build_system_image
build_userdata_image

if [[ "${device_name}" == "hi3516dv300" ]]; then
    source ${OHOS_ROOT_PATH}/build/adapter/images/updater/build_updater_image.sh
fi
