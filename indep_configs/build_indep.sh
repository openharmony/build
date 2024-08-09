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
echo $1 $2 $3
TEST_FILTER=$3
VARIANTS="default"
if [ -n "$4" ]; then
  VARIANTS=$4
fi
rm -rf out
rm -rf .gn

mkdir -p out/$VARIANTS
mkdir -p out/preloader
mkdir -p out/$VARIANTS/build_configs/parts_info
cp -rf build/indep_configs/mapping/component_mapping.json out/$VARIANTS/build_configs
ln -s build/indep_configs/dotfile.gn .gn

export SOURCE_ROOT_DIR="$PWD"

# set python3
HOST_DIR="linux-x86"
HOST_OS="linux"
NODE_PLATFORM="linux-x64"

PYTHON3_DIR=${SOURCE_ROOT_DIR}/prebuilts/python/${HOST_DIR}/current/
PYTHON3=${PYTHON3_DIR}/bin/python3
PYTHON=${PYTHON3_DIR}/bin/python
export PATH=${SOURCE_ROOT_DIR}/prebuilts/build-tools/${HOST_DIR}/bin:${PYTHON3_DIR}/bin:$PATH
if [ -d "binarys/third_party/rust" ];then
    echo "rust directory exists"
    if [ -d "third_party/rust" ]; then
        echo "third_party/rust exists"
        cp -r binarys/third_party/rust/crates third_party/rust
    else
        mkdir -p "third_party/rust"
        cp -r binarys/third_party/rust/crates third_party/rust
    fi
else
    echo "rust directory exists"
fi
${PYTHON3} ${SOURCE_ROOT_DIR}/build/indep_configs/scripts/generate_components.py -hp $1 -sp $2 -v ${VARIANTS} -rp ${SOURCE_ROOT_DIR} -t ${TEST_FILTER}
${PYTHON3} ${SOURCE_ROOT_DIR}/build/indep_configs/scripts/generate_target_build_gn.py -p $2 -rp ${SOURCE_ROOT_DIR} -t ${TEST_FILTER}
${PYTHON3} ${SOURCE_ROOT_DIR}/build/indep_configs/scripts/variants_info_handler.py -rp ${SOURCE_ROOT_DIR} -v ${VARIANTS}
# gn and ninja command
${PYTHON3} ${SOURCE_ROOT_DIR}/build/indep_configs/scripts/gn_ninja_cmd.py -rp ${SOURCE_ROOT_DIR} -v ${VARIANTS}

if [ $? -ne 0 ]; then
  exit 1
fi

rm -rf .gn
ln -s build/core/gn/dotfile.gn .gn

exit 0
