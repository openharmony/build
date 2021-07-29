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

build_tools_path=third_party/e2fsprogs/prebuilt/host/bin
build_image_scripts_path=build/adapter/images/mkimage
image_type="raw"

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
    --sparse-image)
        image_type="sparse"
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

function build_vendor_image() {
    if [[ ! -d "${ohos_build_out_dir}/images" ]]; then
        mkdir ${ohos_build_out_dir}/images
    fi
    # remove images/vendor
    if [[ -d "${ohos_build_out_dir}/images/vendor" ]]; then
        rm -rf ${ohos_build_out_dir}/images/vendor
    fi
    if [[ $USE_OHOS_INIT != true ]]; then
        cp -arf prebuilts/aosp_prebuilt_libs/minisys/vendor ${ohos_build_out_dir}/images/
    else
        mkdir -p ${ohos_build_out_dir}/images/vendor/
    fi

    if [[ -d "${ohos_build_out_dir}/vendor" ]]; then
        cp -arf ${ohos_build_out_dir}/vendor/* ${ohos_build_out_dir}/images/vendor/
    fi
    # remove img
    rm -rf ${ohos_build_out_dir}/images/vendor.img

    # build vendor image
    if [[ $USE_OHOS_INIT == true ]] && [[ $BUILD_IMAGE == true ]]; then
        PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
            ${ohos_build_out_dir}/images/vendor \
            ${build_image_scripts_path}/vendor_image_conf.txt \
            ${ohos_build_out_dir}/images/vendor.img \
            ${image_type}
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build vendor image error.\033[0m"
            exit 1
        fi
    else
        PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
            ${ohos_build_out_dir}/images/vendor \
            prebuilts/aosp_prebuilt_libs/minisys/vendor_image_info.txt \
            ${ohos_build_out_dir}/images/vendor.img \
            ${ohos_build_out_dir}/images/system
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build vendor image error.\033[0m"
            exit 1
        fi
    fi
    echo -e "\033[32m  build vendor image successful.\033[0m"
}


function _update_build_prop() {
    local system_build_prop_file=${ohos_build_out_dir}/images/system/build.prop
    if [[ $USE_OHOS_INIT == true ]] && [[ ! -f "${system_build_prop_file}" ]]; then
        touch ${system_build_prop_file}
    fi
    local ohos_build_prop_file=${OHOS_ROOT_PATH}/build/ohos_system.prop
    if [[ -f "${ohos_build_prop_file}" ]] && [[ -f "${system_build_prop_file}" ]]; then
        echo '' >> ${system_build_prop_file}
        cat ${ohos_build_prop_file} >> ${system_build_prop_file}
    fi
}

function build_system_images_for_musl() {
    cp ${ohos_build_out_dir}/../../common/common/sh  ${ohos_build_out_dir}/images/system/bin/sh
    cp ${ohos_build_out_dir}/../../common/common/toybox  ${ohos_build_out_dir}/images/system/bin/toybox
    cmds_creater=${OHOS_ROOT_PATH}/build/adapter/images/create_init_cmds.sh
    ${cmds_creater} ${ohos_build_out_dir}/images/system/bin
}

function copy_init() {
    cp ${ohos_build_out_dir}/system/etc/init.Hi3516DV300.cfg ${ohos_build_out_dir}/images/root/init.Hi3516DV300.cfg
    cp ${ohos_build_out_dir}/system/etc/init.cfg ${ohos_build_out_dir}/images/root/init.cfg
    cp ${ohos_build_out_dir}/system/etc/init.usb.cfg ${ohos_build_out_dir}/images/root/init.usb.cfg
    cp ${ohos_build_out_dir}/system/etc/init.usb.configfs.cfg ${ohos_build_out_dir}/images/root/init.usb.configfs.cfg
    cp ${ohos_build_out_dir}/system/etc/init.Hi3516DV300.usb.cfg ${ohos_build_out_dir}/images/root/init.Hi3516DV300.usb.cfg
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

    # remove images/system
    if [[ -d "${ohos_build_out_dir}/images/system" ]]; then
        rm -rf ${ohos_build_out_dir}/images/system
    fi
    if [[ $USE_OHOS_INIT != true ]]; then
        cp -arf prebuilts/aosp_prebuilt_libs/minisys/system ${ohos_build_out_dir}/images/
    else
        mkdir -p ${ohos_build_out_dir}/images/system/
    fi
    cp -arf ${ohos_build_out_dir}/system/* ${ohos_build_out_dir}/images/system/

    # update build.prop
    _update_build_prop
    # build for init
    copy_init
    if [[ $BUILD_WITH_MUSL == true ]]; then
        build_system_images_for_musl
        # copy prop.default
        cp prebuilts/aosp_prebuilt_libs/minisys/system/etc/prop.default ${ohos_build_out_dir}/images/system/etc/
    fi
    # remove img
    rm -rf ${ohos_build_out_dir}/images/system.img
    # build system image
    if [[ $USE_OHOS_INIT == true ]] && [[ $BUILD_IMAGE == true ]]; then
        PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
            ${ohos_build_out_dir}/images/system \
            ${build_image_scripts_path}/system_image_conf.txt \
            ${ohos_build_out_dir}/images/system.img \
            ${image_type}
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build system image error.\033[0m"
            exit 1
        fi
    else
        PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
            ${ohos_build_out_dir}/images/system \
            prebuilts/aosp_prebuilt_libs/minisys/system_image_info.txt \
            ${ohos_build_out_dir}/images/system.img \
            ${ohos_build_out_dir}/images/system
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build system image error.\033[0m"
            exit 1
        fi
    fi
    echo -e "\033[32m  build system image successful.\033[0m"
}

function build_userdata_image() {
    if [[ -d "${ohos_build_out_dir}/images/data" ]]; then
        rm -rf ${ohos_build_out_dir}/images/data
    fi
    mkdir ${ohos_build_out_dir}/images/data
    # build userdata image
    if [[ $USE_OHOS_INIT == true ]] && [[ $BUILD_IMAGE == true ]]; then
        PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
            ${ohos_build_out_dir}/images/data \
            ${build_image_scripts_path}/userdata_image_conf.txt \
            ${ohos_build_out_dir}/images/userdata.img \
            ${image_type}
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build userdata image error.\033[0m"
            exit 1
        fi
    else
        PATH=prebuilts/aosp_prebuilt_libs/host_tools/bin:$PATH prebuilts/aosp_prebuilt_libs/host_tools/releasetools/build_image.py \
            ${ohos_build_out_dir}/images/data \
            prebuilts/aosp_prebuilt_libs/minisys/userdata_image_info.txt \
            ${ohos_build_out_dir}/images/userdata.img \
            ${ohos_build_out_dir}/images/system
        if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
            echo "\033[31m  build: build userdata image error.\033[0m"
            exit 1
        fi
    fi
    echo -e "\033[32m  build userdata image successful.\033[0m"
}


function prepare_root() {
    if [[ -d "${ohos_build_out_dir}/images/root" ]]; then
        rm -rf ${ohos_build_out_dir}/images/root
    fi
    if [[ $USE_OHOS_INIT == true ]] && [[ $BUILD_IMAGE == true ]]; then
        mkdir -p ${ohos_build_out_dir}/images/root/
        local dir_list=(dev proc sys)
        pushd ${ohos_build_out_dir}/images/root
            for _path in ${dir_list[@]}
            do
                if [[ ! -d "${_path}" ]]; then
                    mkdir ${_path}
                fi
            done
            ln -s /system/bin bin
            ln -s /system/bin/init init
            ln -s /system/etc etc
            ln -s /system/etc/prop.default default.prop
        popd
    else
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
    fi
}

prepare_root
build_system_image
build_vendor_image
build_userdata_image

if [[ "${device_name}" == "hi3516dv300" ]]; then
    source ${OHOS_ROOT_PATH}/build/adapter/images/updater/build_updater_image.sh
fi
