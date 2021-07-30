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

updater_exe_path="${OHOS_ROOT_PATH}/out/ohos-arm-release/obj/third_party/e2fsprogs/prebuilt/target/bin"
updater_lib_path="${OHOS_ROOT_PATH}/out/ohos-arm-release/obj/third_party/e2fsprogs/prebuilt/target/lib"
updater_out_common="${OHOS_ROOT_PATH}/out/ohos-arm-release/common/common"
updater_minisys="${OHOS_ROOT_PATH}/prebuilts/aosp_prebuilt_libs/minisys"

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
  else
    # For file system tools
    cp -f ${updater_lib_path}/libext2fs.so ${updater_target_out}/system/lib/libext2fs.so
    cp -f ${updater_lib_path}/libext2_com_err.so ${updater_target_out}/system/lib/libext2_com_err.so
    cp -f ${updater_lib_path}/libext2_uuid.so ${updater_target_out}/system/lib/libext2_uuid.so
    cp -f ${updater_lib_path}/libext2_blkid.so ${updater_target_out}/system/lib/libext2_blkid.so
    cp -f ${updater_lib_path}/libext2_misc.so ${updater_target_out}/system/lib/libext2_misc.so
    cp -f ${updater_lib_path}/libext2_quota.so ${updater_target_out}/system/lib/libext2_quota.so
    cp -f ${updater_lib_path}/libext2_e2p.so ${updater_target_out}/system/lib/libext2_e2p.so
    cp -f ${updater_exe_path}/mke2fs ${updater_target_out}/system/bin/mke2fs
    # For toybox
    cp -f ${updater_out_common}/toybox ${updater_target_out}/system/bin/toybox
  fi
  # For UI
  cp -f ${ohos_build_out_dir}/system/lib/libdrm.so ${updater_target_out}/system/lib/libdrm.so
  cp -f ${ohos_build_out_dir}/system/lib/libpng.z.so ${updater_target_out}/system/lib/libpng.z.so
  # For input, copy from ohos
  cp -f ${ohos_build_out_dir}/system/lib/libhdi_input.z.so ${updater_target_out}/system/lib/libhdi_input.z.so
  cp -f ${ohos_build_out_dir}/system/lib/libutils.z.so ${updater_target_out}/system/lib/libutils.z.so
  cp -f ${ohos_build_out_dir}/system/lib/libhilog.so ${updater_target_out}/system/lib/libhilog.so
  cp -f ${ohos_build_out_dir}/system/lib/libhdf_utils.z.so ${updater_target_out}/system/lib/libhdf_utils.z.so
  cp -f ${ohos_build_out_dir}/system/lib/libhilogutil.so ${updater_target_out}/system/lib/libhilogutil.so
  cp -f ${ohos_build_out_dir}/system/lib/libutilsecurec_shared.z.so ${updater_target_out}/system/lib/libutilsecurec_shared.z.so
  cp -f ${ohos_build_out_dir}/system/lib/libhilog_os_adapter.z.so ${updater_target_out}/system/lib/libhilog_os_adapter.z.so
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
  else
    cp -f ${updater_out_common}/sh ${updater_target_out}/system/bin/sh
  fi
}

function install_kernel_modules() {
  cp -f ${ohos_build_out_dir}/vendor/modules/hi3516cv500_base.ko ${updater_target_out}/hi3516cv500_base.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/hi_osal.ko ${updater_target_out}/hi_osal.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/sys_config.ko ${updater_target_out}/sys_config.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/hi3516cv500_sys.ko ${updater_target_out}/hi3516cv500_sys.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/hi3516cv500_vo_dev.ko ${updater_target_out}/hi3516cv500_vo_dev.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/hi3516cv500_hdmi.ko ${updater_target_out}/hi3516cv500_hdmi.ko
  cp -f ${ohos_build_out_dir}/vendor/modules/hifb.ko ${updater_target_out}/hifb.ko
  if [[ ${USE_OHOS_INIT} != true ]]; then
    cp -f ${updater_minisys}/system/bin/insmod ${updater_target_out}/system/bin/insmod
  fi
}

