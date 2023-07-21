#!/usr/bin/env python
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

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file  # noqa: E402


def check(args):
    depfiles = []
    # ignore test related parts/subsystems
    part_allow_set = {'test', 'libc-test', 'libc-test-lib', 'developertest', 'bmssystemtestability'}
    subsystem_allow_set = {'tests'}

    if args.subsystem_name in subsystem_allow_set or args.part_name in part_allow_set:
        return depfiles

    compile_standard_allow_file = args.compile_standard_allow_file
    compile_standard_allow_info = read_json_file(compile_standard_allow_file)
    bundle_file_allow_list = compile_standard_allow_info.get("gn_part_or_subsystem_error", [])
    part_subsystem_info_file = 'build_configs/parts_info/part_subsystem.json'
    data = read_json_file(part_subsystem_info_file)
    if data is None:
        raise Exception(
            "read file '{}' failed.".format(part_subsystem_info_file))
    depfiles.append(part_subsystem_info_file)

    subsystems_name = data.get(args.part_name)
    if subsystems_name is None or subsystems_name == '' or subsystems_name != args.subsystem_name:
        message = f"subsystem name or part name is incorrect, " \
           f"target is {args.target_path}, subsystem name is {args.subsystem_name}, " \
           f"part name is {args.part_name}"
        if args.target_path in bundle_file_allow_list:
            print(f"[0/0] warning: {message}")
        else:
            raise Exception(message)
            
    return depfiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--part-name', required=True)
    parser.add_argument('--subsystem-name', required=True)
    parser.add_argument('--target-path', required=True)
    args = parser.parse_args()

    check(args)

    return 0

if __name__ == '__main__':
    sys.exit(main())
