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

import argparse
import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file

DEL_TARGET = ["//interface/sdk-js:bundle_api"]


def regenerate_sdk_config_file(options):
    sdk_build_public = options.sdk_build_public
    sdk_build_arkts = options.sdk_build_arkts
    sdk_description_file = options.sdk_description_file
    output_sdk_desc_file = options.output_arkts_sdk_desc_file
    info_list = read_json_file(sdk_description_file)
    arkts_sdk_info_list = []
    for info in info_list:
        label = str(info.get("module_label"))
        if label in DEL_TARGET and sdk_build_public == "true":
            continue
        if sdk_build_arkts != "true":
            install_label_str = str(info.get("install_dir"))
            if install_label_str.startswith("ets/ets1.2/"):
                continue
            elif install_label_str.startswith("ets/ets1.1/build-tools/interop"):
                continue
            elif install_label_str.startswith("ets/ets1.1/"):
                info["install_dir"] = str(info.get("install_dir")).replace("ets/ets1.1/", "ets/")
        arkts_sdk_info_list.append(info)
    write_json_file(output_sdk_desc_file, arkts_sdk_info_list)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-description-file', required=True)
    parser.add_argument('--output-arkts-sdk-desc-file', required=True)
    parser.add_argument('--sdk-build-public', required=True)
    parser.add_argument('--sdk-build-arkts', required=True)

    options = parser.parse_args()

    regenerate_sdk_config_file(options)


if __name__ == '__main__':
    sys.exit(main())
