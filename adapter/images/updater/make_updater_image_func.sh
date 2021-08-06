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

function install_common_libraries() {
  if [[ ${USE_OHOS_INIT} != true ]]; then
    cp -f ${updater_minisys}/system/lib/libsparse.so ${updater_target_out}/system/lib/libsparse.so
    # For file system tools
    cp -f ${updater_minisys}/system/lib/libext2fs.so ${updater_target_out}/system/lib/libext2fs.so
    cp -f ${updater_minisys}/system/lib/libext2_com_err.so ${updater_target_out}/system/lib/libext2_com_err.so
    cp -f ${updater_minisys}/system/lib/libext2_uuid.so ${updater_target_out}/system/lib/libext2_uuid.so
    cp -f ${updater_minisys}/system/lib/libext2_blkid.so ${updater_target_out}/system/lib/libext2_blkid.so
    cp -f ${updater_minisys}/system/lib/libext2_misc.so ${updater_target_out}/system/lib/libext2_misc.so
    cp -f ${updater_minisys}/system/lib/libext2_quota.so ${updater_target_out}/system/lib/libext2_quota.so
    cp -f ${updater_minisys}/system/lib/libext2_e2p.so ${updater_target_out}/system/lib/libext2_e2p.so
    cp -f ${updater_minisys}/system/bin/mke2fs ${updater_target_out}/system/bin/mke2fs
    # For toybox
    cp -f ${updater_minisys}/system/bin/toybox ${updater_target_out}/system/bin/toybox
    cp -f ${updater_minisys}/system/lib/liblog.so ${updater_target_out}/system/lib/liblog.so
    cp -f ${updater_minisys}/system/lib/libselinux.so ${updater_target_out}/system/lib/libselinux.so
    cp -f ${updater_minisys}/system/lib/libcutils.so ${updater_target_out}/system/lib/libcutils.so
    cp -f ${updater_minisys}/system/lib/libbase.so ${updater_target_out}/system/lib/libbase.so
    cp -f ${updater_minisys}/system/lib/libprocessgroup.so ${updater_target_out}/system/lib/libprocessgroup.so
    cp -f ${updater_minisys}/system/lib/libcrypto.so ${updater_target_out}/system/lib/libcrypto.so
    cp -f ${updater_minisys}/system/lib/libz.so ${updater_target_out}/system/lib/libz.so
    cp -f ${updater_minisys}/system/lib/libpcre2.so ${updater_target_out}/system/lib/libpcre2.so
    cp -f ${updater_minisys}/system/lib/libpackagelistparser.so ${updater_target_out}/system/lib/libpackagelistparser.so
    cp -f ${updater_minisys}/system/lib/libcgrouprc.so ${updater_target_out}/system/lib/libcgrouprc.so
  fi
}

function install_standard_libraries() {
  if [[ ${USE_OHOS_INIT} != true ]]; then
    cp -f ${updater_minisys}/system/lib/bootstrap/libc.so ${updater_target_out}/system/lib/libc.so
    cp -f ${updater_minisys}/system/lib/bootstrap/libdl.so ${updater_target_out}/system/lib/libdl.so
    cp -f ${updater_minisys}/system/lib/bootstrap/libm.so ${updater_target_out}/system/lib/libm.so
    cp -f ${updater_minisys}/system/bin/bootstrap/linker ${updater_target_out}/system/bin/linker
    cp -f ${updater_minisys}/system/lib/libc++.so ${updater_target_out}/system/lib/libc++.so
    cp -f ${updater_minisys}/system/lib/ld-android.so ${updater_target_out}/system/lib/ld-android.so
    cp -f ${updater_minisys}/system/bin/sh ${updater_target_out}/system/bin/sh
  fi
}

function install_kernel_modules() {
  if [[ ${USE_OHOS_INIT} != true ]]; then
    cp -f ${updater_minisys}/system/bin/insmod ${updater_target_out}/system/bin/insmod
  fi
}

