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

find_root() {
    local target="$1"
    local current_dir=$(pwd)
    local found_dir=""

    while [[ "$current_dir" != "/" ]]; do
        if [[ -e "$current_dir/$target" ]]; then
            found_dir="$current_dir"
            break
        fi
        current_dir=$(dirname "$current_dir")
    done

    if [[ -n "$found_dir" ]]; then
        echo "$found_dir"
        return 0
    else
        echo "$target directory not found" >&2
        return 1
    fi
}

target_path="build/prebuilts_service/shell/init_ohpm.sh"
result_dir=$(find_root "$target_path")

if [[ $? -eq 0 ]]; then
    code_dir="$result_dir"
else
    echo "$target directory not found" >&2
    exit 1
fi
# set nodejs and ohpm
EXPECTED_NODE_VERSION="14.21.1"
NODE_PLATFORM="linux-x64"

export PATH=${code_dir}/prebuilts/build-tools/common/nodejs/node-v${EXPECTED_NODE_VERSION}-${NODE_PLATFORM}/bin:$PATH
echo ${code_dir}/prebuilts/build-tools/common/nodejs/node-v${EXPECTED_NODE_VERSION}-${NODE_PLATFORM}/bin
export NODE_HOME=${code_dir}/prebuilts/build-tools/common/nodejs/node-v${EXPECTED_NODE_VERSION}-${NODE_PLATFORM}
export PATH=${code_dir}/prebuilts/build-tools/common/oh-command-line-tools/ohpm/bin:$PATH

echo -e "\033[32m[OHOS INFO] Node.js version check passed!\033[0m"
npm config set registry https://repo.huaweicloud.com/repository/npm/
npm config set @ohos:registry https://repo.harmonyos.com/npm/
npm config set strict-ssl false
npm config set lockfile false
cat $HOME/.npmrc | grep 'lockfile=false' > /dev/null || echo 'lockfile=false' >> $HOME/.npmrc > /dev/null

function init_ohpm() {
  TOOLS_INSTALL_DIR="${code_dir}/prebuilts/build-tools/common"
  pushd ${TOOLS_INSTALL_DIR} > /dev/null
    OHPM_HOME=${TOOLS_INSTALL_DIR}/../../tool/command-line-tools/ohpm/bin
    chmod +x ${OHPM_HOME}/ohpm
    export PATH=${OHPM_HOME}:$PATH
    chmod +x ${OHPM_HOME}/init
    ${OHPM_HOME}/init > /dev/null
    echo "[OHOS INFO] Current ohpm version is $(ohpm -v)"
    ohpm config set registry https://repo.harmonyos.com/ohpm/
    ohpm config set strict_ssl false
    ohpm config set log_level debug
  popd > /dev/null
  if [[ -d "$HOME/.hvigor" ]]; then
    rm -rf $HOME/.hvigor/daemon $HOME/.hvigor/wrapper
  fi
  mkdir -p $HOME/.hvigor/wrapper/tools
  echo '{"dependencies": {"pnpm": "7.30.0"}}' > $HOME/.hvigor/wrapper/tools/package.json
  pushd $HOME/.hvigor/wrapper/tools > /dev/null
    echo "[OHOS INFO] installing pnpm..."
    npm install --silent > /dev/null
  popd > /dev/null
  HVIGORW_HOME=${TOOLS_INSTALL_DIR}/../../tool/command-line-tools/hvigor/bin/hvigorw
  chmod +x ${HVIGORW_HOME}
  mkdir -p $HOME/.ohpm
  echo '{"devDependencies":{"@ohos/hypium":"1.0.6"}}' > $HOME/.ohpm/oh-package.json5
  pushd $HOME/.ohpm > /dev/null
    echo "[OHOS INFO] installing hypium..."
    ohpm install > /dev/null
  popd > /dev/null
}

init_ohpm
echo "======init_ohpm finished!======"