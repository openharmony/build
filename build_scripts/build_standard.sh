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

echo "build standard system..."
echo "---------------------------------------"
echo $@

script_path=$(cd $(dirname $0);pwd)

# parse params
source ${script_path}/parse_params.sh

system_type="standard"

source ${script_path}/build_common.sh


function main() {
  # build ohos
  do_make_ohos

  if [[ "${build_only_gn}" == true ]]; then
    return
  fi
  build_target=$(echo ${build_target} | xargs)
  echo "build_target='${build_target}'"
  if [[ "${build_target}" == "build_ohos_sdk" ]]; then
    echo -e "\033[32m  build ohos-sdk successful.\033[0m"
    return
  fi

  ohos_build_root_dir="${OHOS_ROOT_PATH}/out/release"
  if [[ "${target_cpu}" == "arm" ]]; then
    ohos_build_root_dir="${OHOS_ROOT_PATH}/out/ohos-arm-release"
  fi

  # build images
  build/adapter/images/build_image.sh --device-name ${device_name} \
    --ohos-build-out-dir ${ohos_build_root_dir}/packages/phone
}

main
