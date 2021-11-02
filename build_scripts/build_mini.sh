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
  --build-target | -T | -t)
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
  --build-gnargs-file)
    shift
    build_gnargs_file="$1"
    ;;
  --build-only-gn)
    build_only_gn=true;;
  -* | *)
    args+=" $1"
    ;;
  esac
  shift
done

source out/preloader/${product_name}/build.prop
# build lite
build_cmd="python3 build.py -p ${product_name}@${product_company} ${args}"

if [ ! -z "${build_target}" ]; then
    build_cmd+=" -T ${build_target}"
fi

build_cmd+=" --compact-mode"

if [[ -f "${build_gnargs_file}" ]]; then
  build_cmd+=" --gn-args=\""
  for _line in $(cat "${build_gnargs_file}"); do
    build_cmd+="${_line} "
  done
  build_cmd+="is_mini_system=true\""
else
  build_cmd+=" --gn-args=\"is_mini_system=true\""
fi

eval ${build_cmd}
