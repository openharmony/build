#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import argparse
import os
import sys
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-description-file', required=True)
    parser.add_argument('--output-hap-build-sdk-desc-file', required=True)

    options = parser.parse_args()
    sys.path.append(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from scripts.util.file_utils import read_json_file, write_json_file
    info_list = read_json_file(options.sdk_description_file)
    new_info_list = []
    for info in info_list:
        if info.get("install_dir").startswith("previewer"):
            continue
        if "linux" not in info.get("target_os"):
            continue
        new_info_list.append(info)
    write_json_file(options.output_hap_build_sdk_desc_file, new_info_list)


if __name__ == '__main__':
    sys.exit(main())