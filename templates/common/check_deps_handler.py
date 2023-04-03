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

import os
import json
import sys
import argparse


sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file  # noqa: E402


def check_deps_with_module(parts_modules_info_file, current_part_name, deps, target_path):
    parts_module_data = read_json_file(parts_modules_info_file)
    parts_module_lists = []
    check_dep_flag = 0
    for parts_module in parts_module_data.get("parts"):
        if parts_module.get("part_name") == current_part_name:
            parts_module_lists = parts_module["module_list"]
            break
    for dep in deps:
        dep_path = dep[2:dep.find(':')]
        if dep_path.find('third_party') != -1:
            continue
        for module in parts_module_lists:
            module = module[2:module.find(':')]
            if not dep_path.startswith(module):
                check_dep_flag += 1
        if check_dep_flag == len(parts_module_lists):
            print("WARNING:deps validation part_name: '{}', target: '{}', dep: '{}' failed!!!"
                    .format(current_part_name, target_path, dep))
            check_dep_flag = 0


def check_deps_with_parts(current_part_name, deps, target_path, part_path):
    for dep in deps:
        dep_path = dep[2:dep.find(':')]
        if dep_path.find('third_party') != -1:
            continue
        if not dep_path.startswith(part_path):
            print("WARNING:deps validation part_name: '{}', target: '{}', dep: '{}' failed!!!"
                    .format(current_part_name, target_path, dep))


def check_wrong_used_deps(parts_path_info_file, path_parts_info_file, parts_modules_info_file,
                            deps, current_part_name, target_path_val):
    if current_part_name.find('test') != -1:
        return 0

    parts_path_data = read_json_file(parts_path_info_file)
    part_path = parts_path_data.get(current_part_name)
    if part_path is None:
        print("part_name: '{}' path is not exist, please check target: '{}' "
                .format(current_part_name, target_path_val))
        return 0

    path_parts_data = read_json_file(path_parts_info_file)
    path_to_part = path_parts_data.get(part_path)

    if len(path_to_part) > 1:
        check_deps_with_module(parts_modules_info_file, current_part_name, deps, target_path_val)
    else:
        check_deps_with_parts(current_part_name, deps, target_path_val, part_path)
    return 0


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--parts-path-info-file', required=True)
    parser.add_argument('--path-parts-info-file', required=True)
    parser.add_argument('--parts-modules-info-file', required=True)
    parser.add_argument('--deps', nargs='*', required=True)
    parser.add_argument('--current-part-name', required=True)
    parser.add_argument('--target-path-val', required=True)
    args = parser.parse_args(argv)
    check_wrong_used_deps(args.parts_path_info_file, args.path_parts_info_file, args.parts_modules_info_file,
                            args.deps, args.current_part_name, args.target_path_val)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
