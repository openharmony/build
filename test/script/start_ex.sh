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

script_path=$(cd $(dirname $0);pwd)
pre_dir_path=$(dirname ${script_path})
pre_dir_path=$(dirname ${pre_dir_path})
root_path=$(dirname ${pre_dir_path})
echo $root_path

CONFIG_PATH=$root_path/build/test/example/build_example.json
SRC_BUNDLE_PATH=$root_path/build/test/example/test_build.json
DEST_BUNDLE_PATH=$root_path/build/common/bundle.json
echo $CONFIG_PATH



function read_file() {
    FILENAME=$1;KEY=$2
    RESULT=$(cat $FILENAME | grep $KEY | awk -F\" '{ print $4 }')
    echo $RESULT
}

function generate_build_option_report() {
    option_report_path=$(read_file $CONFIG_PATH option_report_path)
    option_script_path=$(read_file $CONFIG_PATH option_script_path)
    pytest -vs --html $root_path$option_report_path $root_path$option_script_path
    pkill -f '/pyd.py --root .*/.pycache --start'
}

function generate_gn_template_report() {
    gn_template_report_path=$(read_file $CONFIG_PATH gn_template_report_path)
    gn_template_script_path=$(read_file $CONFIG_PATH gn_template_script_path)
    pytest -vs --html $root_path$gn_template_report_path $root_path$gn_template_script_path
}

function generate_performance_report() {
    performance_script_path=$(read_file $CONFIG_PATH performance_script_path)
    python3 $root_path$performance_script_path
}

function start() {
    if [[ $# -eq 1 && $1 == 'all' ]]; then
      generate_build_option_report
      generate_performance_report
      generate_gn_template_report
    elif [[ $# -eq 1 && $1 == 'option' ]]; then
      generate_build_option_report
    elif [[ $# -eq 1 && $1 == 'template' ]]; then
      generate_gn_template_report
    elif [[ $# -eq 1 && $1 == 'performance' ]]; then
      generate_performance_report
    else
      echo 'args wrong'
    fi
}

rm -rf $root_path/out
product_path=$(read_file $CONFIG_PATH product_path)
mkdir -p $root_path$product_path

cp $SRC_BUNDLE_PATH $DEST_BUNDLE_PATH

start "$@"




