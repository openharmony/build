#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import sys
import json
import os
import argparse
import shutil
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import write_file  # noqa: E402
from scripts.util import build_utils  # noqa: E402


def copy_file(suite_path: str, template_path: str, target_path: str):
    file_list = []
    name_list = []
    template_path = os.path.join(template_path, "src")

    if not os.path.exists(suite_path):
        raise Exception("suite path '{}' doesn't exist.".format(suite_path))

    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    os.makedirs(target_path, exist_ok=True)
    shutil.copytree(template_path, os.path.join(target_path, "src"))

    js_dest_path = os.path.join(target_path,
        "src", "main", "js", "default", "test")
    for root, dirs, files in os.walk(suite_path):
        for item in files:
            if item.endswith('.js'):
                name_list.append(item)
                file_list.append(os.path.join(root, item))
    
    for file in file_list:
        shutil.copy2(file, js_dest_path)
    write_list_file(js_dest_path, name_list)


def write_list_file(dest_path: str, name_list: list):
    with open(os.path.join(dest_path, "List.test.js"), 'a') \
        as list_data:
        for name in name_list:
            list_data.write("require('./%s')\n" % name)


def get_hap_json(target_name: str, test_output_dir: str):
    os.makedirs(test_output_dir, exist_ok=True)
    json_file = os.path.join(test_output_dir, target_name + ".json")
    json_info_data = {"driver": {
       "type": "JSUnitTest"
    }}
    with open(json_file, 'w') as out_file:
        json.dump(json_info_data, out_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite_path', required=True)
    parser.add_argument('--template_path', required=True)
    parser.add_argument('--target_path', required=True)
    parser.add_argument('--test_output_dir', required=True)
    parser.add_argument('--target_name', required=True)
    args = parser.parse_args()

    copy_file(args.suite_path, args.template_path, args.target_path)
    get_hap_json(args.target_name, args.test_output_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
