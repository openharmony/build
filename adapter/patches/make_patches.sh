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

system_type=large

while test $# -gt 0
do
  case "$1" in
  --source-root-dir)
    shift
    source_root_dir="$1"
    ;;
  --system-type)
    shift
    system_type="$1"
    ;;
  -* | *)
    echo "Unrecognized option: $1"
    exit 1
    ;;
  esac
  shift
done

if [[ "${source_root_dir}" == "" ]]; then
  echo "source_root_dir cannot be empty."
  exit 1
fi
if [[ ! -d "${source_root_dir}" ]]; then
  echo "source_root_dir is incorrect."
  exit 1
fi

function make_patches() {
  echo "make patches... system_type=${system_type}"
  _patches_root_path="third_party/aosp/patches"
  _patches_path="${_patches_root_path}/10.0.0_r2"
  if [[ "${system_type}" == "standard" ]]; then
    _patches_path="${_patches_root_path}/10.0.0_r2_standard"
  fi
  ${source_root_dir}/${_patches_path}/make_patch.sh
}

make_patches
