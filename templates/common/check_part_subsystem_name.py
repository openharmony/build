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


def main():
    # ignore test related parts/subsystems
    part_allow_set = {'test', 'libc-test', 'libc-test-lib', 'developertest', 'bmssystemtestability'}
    subsystem_allow_set = {'tests'}

    parser = argparse.ArgumentParser()
    parser.add_argument('--part-name', required=True)
    parser.add_argument('--subsystem-name', required=True)
    parser.add_argument('--target-path', required=True)
    parser.add_argument('--part-subsystem-info-file', required=True)
    args = parser.parse_args()

    if args.subsystem_name in subsystem_allow_set or args.part_name in part_allow_set:
        return 0

    part_subsystem_info_file = 'build_configs/parts_info/part_subsystem.json'
    if args.part_subsystem_info_file:
        part_subsystem_info_file = args.part_subsystem_info_file
    if not os.path.exists(part_subsystem_info_file):
        raise Exception(
            "file '{}' does not exits.".format(part_subsystem_info_file))

    data = read_json_file(part_subsystem_info_file)
    if data is None:
        raise Exception(
            "read file '{}' failed.".format(part_subsystem_info_file))

    subsystems_name = data.get(args.part_name)
    if subsystems_name is None or subsystems_name == '' or subsystems_name != args.subsystem_name:
        print("warning: subsystem name or part name is incorrect, target is {}, subsystem name is {}, part name is {}"
            .format(args.target_path, args.subsystem_name, args.part_name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
