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

import argparse
import json
import os
import time
import stat
import utils


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-p", "--input_path",
        default=r"./", type=str,
        help="Path of source code",
    )
    parser.add_argument(
        "-rp", "--root_path",
        default=r"./", type=str,
        help="Path of root",
    )
    parser.add_argument(
        "-t", "--test",
        default=1, type=int,
        help="whether the target contains test type. default 0 , choices: 0 or 1 2",
    )
    args = parser.parse_args()
    return args


def _judge_type(element, deps_list: list):
    if isinstance(element, dict):
        for k, v in element.items():
            _judge_type(v, deps_list)
    elif isinstance(element, list):
        for v in element:
            _judge_type(v, deps_list)
    elif isinstance(element, str):
        deps_list.append(element)


def _inner_kits_name(inner_kits_list, deps_list):
    if inner_kits_list:
        for k in inner_kits_list:
            deps_list.append(k['name'])


def _output_build_gn(deps_list, output_path, _test_check):
    file_name = os.path.join(output_path, 'BUILD.gn')
    if os.path.exists(file_name):
        os.remove(file_name)
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(file_name, flags, modes), 'w') as f:
        f.write('import("//build/ohos_var.gni")\n')
        f.write('\n')
        f.write('group("default") {\n')
        if _test_check:
            f.write('    testonly = true\n')
        f.write('    deps = [\n')
        for i in deps_list:
            f.write(f"        \"{i}\",\n")
        f.write('    ]\n')
        f.write('}\n')


def _get_bundle_path(source_code_path):
    bundle_paths = dict()
    for root, dirs, files in os.walk(source_code_path):
        for file in files:
            if file.endswith("bundle.json"):
                bundle_paths.update({os.path.join(root, file): root})
    return bundle_paths


def _get_src_part_name(src_bundle_paths):
    _name = ''
    _path = ''
    _bundle_path = ''
    for src_bundle_path, v_path in src_bundle_paths.items():
        src_bundle_json = utils.get_json(src_bundle_path)
        part_name = ''
        try:
            part_name = src_bundle_json['component']['name']
        except KeyError:
            print(f'--get bundle json component name error--')
        if part_name.endswith('_lite'):
            pass
        else:
            _name = part_name
            _bundle_path = src_bundle_path
            _path = v_path
    return _bundle_path, _path


def _target_handle(ele, build_data, deps_list, _test_check):
    if ele not in ['inner_kits', 'test', 'inner_api']:
        _judge_type(build_data[ele], deps_list)
    elif ele in ['inner_kits', 'inner_api']:
        inner_kits_list = build_data[ele]
        _inner_kits_name(inner_kits_list, deps_list)

    if _test_check == 1 and ele == 'test':
        inner_kits_list = build_data[ele]
        for k in inner_kits_list:
            deps_list.append(k)


def main():
    args = _get_args()
    source_code_path = args.input_path
    _test_check = args.test
    deps_list = list()
    bundle_paths = _get_bundle_path(source_code_path)
    _bundle_path, dir_path = _get_src_part_name(bundle_paths)
    bundle_json = utils.get_json(_bundle_path)
    build_data = dict()
    try:
        build_data = bundle_json["component"]["build"]
    except KeyError:
        print(f'--get bundle json component build dict error--')
    if _test_check != 2:
        for ele in build_data.keys():
            _target_handle(ele, build_data, deps_list, _test_check)
    elif _test_check == 2:
        inner_kits_list = build_data.get('test')
        deps_list = []
        for k in inner_kits_list:
            deps_list.append(k)

    output_path = os.path.join(args.root_path, 'out')
    _output_build_gn(deps_list, output_path, _test_check)


if __name__ == '__main__':
    main()
