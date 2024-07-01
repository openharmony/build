#!/bin/bash
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
SOURCE_FILE_DIR=${1}
TARGET_KO_NAME=${2}
OUT_DIR=${3}
PROJECT_DIR=${4}
DEVICE_NAME=${5}
DEVICE_ARCH=${6}

args=("$@")
after_args=("${args[@]:6}")

obj_list=""
for item in "${after_args[@]}"
do
  obj_list+="$item.o"
  obj_list+="&"
done

pushd ${SOURCE_FILE_DIR}
cp ${PROJECT_DIR}/build/templates/kernel/linux-6.6/Makefile .
cp ${PROJECT_DIR}/out/kernel/OBJ/linux-6.6/certs/signing_key.pem .
export PATH=${PROJECT_DIR}/out/kernel/OBJ/linux-6.6/scripts/:$PATH

make PROJECTDIR=${PROJECT_DIR} DEVICENAME=${DEVICE_NAME} DEVICEARCH=${DEVICE_ARCH} TARGETKONAME=${TARGET_KO_NAME} OBJLIST=${obj_list}
sign-file sha512 signing_key.pem signing_key.pem *.ko
if [ -d "${OUT_DIR}" ]; then
    echo "The ko build out dir exist"
else
    mkdir ${OUT_DIR}
fi

cp -f *.ko ${OUT_DIR}
make clean
rm -f Makefile
rm -rf signing_key.pem
exit 0
