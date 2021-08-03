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

function build_vendor_image() {
    if [[ ! -d "${ohos_build_out_dir}/images" ]]; then
        mkdir ${ohos_build_out_dir}/images
    fi
    # remove images/vendor
    if [[ -d "${ohos_build_out_dir}/images/vendor" ]]; then
        rm -rf ${ohos_build_out_dir}/images/vendor
    fi
    mkdir -p ${ohos_build_out_dir}/images/vendor/

    if [[ -d "${ohos_build_out_dir}/vendor" ]]; then
        cp -arf ${ohos_build_out_dir}/vendor/* ${ohos_build_out_dir}/images/vendor/
    fi
    # remove img
    rm -rf ${ohos_build_out_dir}/images/vendor.img

    # build vendor image
    PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
        ${ohos_build_out_dir}/images/vendor \
        ${build_image_scripts_path}/vendor_image_conf.txt \
        ${ohos_build_out_dir}/images/vendor.img \
        ${image_type}
    if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
        echo "\033[31m  build: build vendor image error.\033[0m"
        exit 1
    fi
    echo -e "\033[32m  build vendor image successful.\033[0m"
}

function copy_init() {
    cp ${ohos_build_out_dir}/system/etc/init.Hi3516DV300.cfg ${ohos_build_out_dir}/images/root/init.Hi3516DV300.cfg
    cp ${ohos_build_out_dir}/system/etc/init.cfg ${ohos_build_out_dir}/images/root/init.cfg
    cp ${ohos_build_out_dir}/system/etc/init.usb.cfg ${ohos_build_out_dir}/images/root/init.usb.cfg
    cp ${ohos_build_out_dir}/system/etc/init.usb.configfs.cfg ${ohos_build_out_dir}/images/root/init.usb.configfs.cfg
    cp ${ohos_build_out_dir}/system/etc/init.Hi3516DV300.usb.cfg ${ohos_build_out_dir}/images/root/init.Hi3516DV300.usb.cfg
}

function build_system_image() {
    if [[ ! -d "${ohos_build_out_dir}/images" ]]; then
        mkdir ${ohos_build_out_dir}/images
    fi

    # remove images/system
    if [[ -d "${ohos_build_out_dir}/images/system" ]]; then
        rm -rf ${ohos_build_out_dir}/images/system
    fi
    mkdir -p ${ohos_build_out_dir}/images/system/
    cp -arf ${ohos_build_out_dir}/system/* ${ohos_build_out_dir}/images/system/

    # build for init
    copy_init
    # remove img
    rm -rf ${ohos_build_out_dir}/images/system.img
    # build system image
    PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
        ${ohos_build_out_dir}/images/system \
        ${build_image_scripts_path}/system_image_conf.txt \
        ${ohos_build_out_dir}/images/system.img \
        ${image_type}
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
    # build userdata image
    PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
        ${ohos_build_out_dir}/images/data \
        ${build_image_scripts_path}/userdata_image_conf.txt \
        ${ohos_build_out_dir}/images/userdata.img \
        ${image_type}
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
    mkdir -p ${ohos_build_out_dir}/images/root/
    local dir_list=(config dev proc sys)
    pushd ${ohos_build_out_dir}/images/root
        for _path in ${dir_list[@]}
        do
            if [[ ! -d "${_path}" ]]; then
                mkdir ${_path}
            fi
        done
        ln -s /system/bin bin
        ln -s /system/init init
        ln -s /system/etc etc
    popd
}

prepare_root
build_system_image
build_vendor_image
build_userdata_image

source ${OHOS_ROOT_PATH}/build/adapter/images/updater/build_updater_image.sh
