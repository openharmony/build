#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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
import os
import argparse
import shutil
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

def remove_dir(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)

def copy_file(fuzz_config_file_path, fuzz_config_file_output_path):
    if not os.path.exists(fuzz_config_file_path):
        raise Exception("fuzz_config_file_path '{}' doesn't exist.".format(fuzz_config_file_path))
    target_file_path = os.path.join(fuzz_config_file_output_path, os.path.basename(fuzz_config_file_path))
    if os.path.exists(target_file_path):
        try:
            shutil.rmtree(target_file_path)
        except:
            if os.path.isdir(target_file_path):
                remove_dir(target_file_path)
            else:
                os.remove(target_file_path)
    shutil.copytree(fuzz_config_file_path, target_file_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fuzz-config-file-path', required=True)
    parser.add_argument('--fuzz-config-file-output-path', required=True)
    args = parser.parse_args()

    copy_file(args.fuzz_config_file_path, args.fuzz_config_file_output_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
