#!/bin/bash
# Copyright (c) 2025 Huawei Device Co., Ltd.
# provide a sandbox script to isolate inputs dir for action task
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --script-file)
      shift
      script_file="$1"
      ;;
    --sandbox-metadata)
      shift
      sandbox_metadata="$(realpath "$1")"
      ;;
    --debug)
      # current only print debug mode hint, can remain sandbox directory to debug
      echo "execute sandbox with debug mode"
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "invalid option param $1"
      exit 1
      ;;
  esac
  shift
done

check_param() {
  if [ ! -f "${script_file}" ]; then
    echo "action script: ${script_file} not exists."
    exit 1
  fi

  if [ ! -f "${sandbox_metadata}" ]; then
    echo "action metadata file: ${sandbox_metadata} not exists."
    exit 1
  fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  check_param

  exec_param="/usr/bin/env"

  action_cmd="${exec_param} ${script_file} "
  action_cmd+=$(printf "%q " "$@")

  # directory isolation based on namespace, mount and chroot, currnt only print origin action command
  echo "${action_cmd}"
  ${action_cmd}
fi
