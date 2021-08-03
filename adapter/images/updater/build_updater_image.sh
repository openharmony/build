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

updater_target_out="${ohos_build_out_dir}/images/updater"
CONFIG_BOARD_UPDATER_PARTITION_SIZE=20971520

function prepare_updaterimage_dirs() {
  mkdir -p ${updater_target_out}
  mkdir -p ${updater_target_out}/system/bin
  mkdir -p ${updater_target_out}/system/lib
  mkdir -p ${updater_target_out}/proc
  mkdir -p ${updater_target_out}/sys
  mkdir -p ${updater_target_out}/dev
  mkdir -p ${updater_target_out}/etc
}

function install_updaterimage_depends() {
  install_standard_libraries
  install_common_libraries
  install_kernel_modules
}

function build_updater_image_for_musl() {
  cp ${ohos_build_out_dir}/system/bin/ld-musl-arm.so.1 ${updater_target_out}/system/bin/ld-musl-arm.so.1

  if [[ ! -d "${updater_target_out}/system/lib/musl" ]]; then
    mkdir ${updater_target_out}/system/lib/musl
  fi
  cp ${ohos_build_out_dir}/system/lib/musl/libc++.so ${updater_target_out}/system/lib/musl/libc++.so

  if [[ ! -d "${updater_target_out}/system/etc" ]]; then
    mkdir ${updater_target_out}/system/etc
  fi
  cp ${ohos_build_out_dir}/system/etc/ld-musl-arm.path ${updater_target_out}/system/etc/ld-musl-arm.path
}

function build_updater_image() {

  echo "ohos_build_out_dir = ${ohos_build_out_dir}"

  prepare_updaterimage_dirs

  if [[ -d "${ohos_build_out_dir}/updater" ]]; then
    cp -arf ${ohos_build_out_dir}/updater/* ${updater_target_out}/
  fi

  if [[ $USE_OHOS_INIT == true ]]; then
    build_updater_image_for_musl
  fi
  install_updaterimage_depends
  if [ -e "${ohos_build_out_dir}/images/updater.img" ]; then
    rm -rf ${ohos_build_out_dir}/images/updater.img
  fi
  cd ${updater_target_out}
  ln -s /bin/init init
  cd -
  # Build updater image
  PATH=${build_tools_path}:${build_image_scripts_path}:$PATH mkimages.py \
      ${ohos_build_out_dir}/images/updater \
      ${build_image_scripts_path}/updater_image_conf.txt \
      ${ohos_build_out_dir}/images/updater.img \
      ${image_type}
  if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
    echo "\033[31m  build: build updater image error.\033[0m"
    exit 1
  fi
  echo -e "\033[32m  build updater image successful.\033[0m"
}

source ${OHOS_ROOT_PATH}/build/adapter/images/updater/make_updater_image_func.sh
build_updater_image
