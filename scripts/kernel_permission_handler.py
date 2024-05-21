#!/usr/bin/env python
# -*- coding: utf-8 -*-
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


import json
import subprocess
import sys


def check_json_value(json_data):
    for key, value in json_data.items():
        if not isinstance(value, (bool, str, list)):
            return False
        if isinstance(value, list):
            if not all(isinstance(item, str) for item in value):
                return False
    return True


def check_json_content(json_data):
    if len(json_data) == 1 and "kernelpermission" in json_data:
        json_data = json_data["kernelpermission"]
        return check_json_value(json_data)
    else:
        return False
    
    
def check_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
        if check_json_content(json_data):
            return True
        else:
            print("kernel_permission.json is invalid")
            return False
    except FileNotFoundError:
        print("kernel_permission.json not found")
        return False
    except json.JSONDecodeError:
        print("kernel_permission.json doesn't conform to json specification")
        return False
    except Exception:
        print("kernel_permission.json not found")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/library.so")
        sys.exit(1)

    so_path = sys.argv[1]

    if (check_json_file("kernel_permission.json")):
        command = ['llvm-objcopy', '--add-section', '.kernelpermission=kernel_permission.json', so_path]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("llvm-objcopy executed successfully")
        else:
            print("llvm-objcopy failed")
            print("Error:", result.stderr)
