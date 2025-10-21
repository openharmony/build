#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import argparse
import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file


def remove_cangjie_form_sdk_config_file(sdk_description_file: str):
    info_list = read_json_file(sdk_description_file)
    result = []
    for info in info_list:
        install_label_str = str(info.get('install_dir'))
        if install_label_str.startswith('cangjie/'):
            continue
        result.append(info)

    write_json_file(sdk_description_file, result)


def remove_cangjie_form_sdk_delivery_list(sdk_delivery_list: str, output_sdk_delivery_list: str):
    data = read_json_file(sdk_delivery_list)
    for platform in data.keys():
        data[platform]['checkDirectories'] = [
                directory for directory in data[platform]['checkDirectories']
                if not directory.startswith(f'{platform}/cangjie/')
        ]

    write_json_file(output_sdk_delivery_list, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-description-file', required=True)
    parser.add_argument('--sdk-delivery-list', required=True)
    parser.add_argument('--output-sdk-delivery-list', required=True)

    options = parser.parse_args()

    remove_cangjie_form_sdk_config_file(options.sdk_description_file)
    remove_cangjie_form_sdk_delivery_list(options.sdk_delivery_list, options.output_sdk_delivery_list)


if __name__ == '__main__':
    sys.exit(main())
