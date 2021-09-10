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

echo "build lite system..."
echo "---------------------------------------"
echo $@

script_path=$(cd $(dirname $0);pwd)

# parse params
args=""

while test $# -gt 0
do
  case "$1" in
  --product-name)
    shift
    product_name="$1"
    ;;
  --device-name)
    shift
    ;;
  --target-cpu)
    shift
    ;;
  --target-os)
    shift
    ;;
  --ccache)
    ;;
  --build-target | -t)
    shift
    build_target="${build_target} $1"
    ;;
  --jobs)
    shift
    jobs="$1"
    ;;
  --export-para)
    shift
    PARAM1=$(echo "$1" | sed 's/\(.*\):\(.*\)/\1/')
    PARAM2=$(echo "$1" | sed 's/.*://')
    export $PARAM1=$PARAM2
    ;;
  -* | *)
    args+=" $1"
    ;;
  esac
  shift
done

source out/build_configs/${product_name}/preloader/build.prop
# build lite
python3 build.py -p ${product_name}@${product_company} ${args}
