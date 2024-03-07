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


def get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-sp",
        "--source-code-path",
        default=r".",
        type=str,
        help="Path of source code",
    )
    parser.add_argument(
        "-hp",
        "--hpmcache-path",
        default=r".",
        type=str,
        help="Path of .hpmcache",
    )
    args = parser.parse_args()
    return args


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(' {} runtime is：{}'.format(os.path.basename(__file__), end_time - start_time))
        return result

    return wrapper


def _get_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"can not find file: {file_path}.")
    return data


def get_dependence_json(_path) -> dict:
    dependences_path = os.path.join(_path, 'dependences.json')
    _json = _get_json(dependences_path)
    return _json


def _get_bundle_path(hpm_cache_path, dependences_json, part_name):
    bundle_path = (hpm_cache_path +
                   dependences_json[part_name]['installPath'] + os.sep + 'bundle.json')
    return bundle_path


def _get_src_bundle_path(source_code_path):
    bundle_paths = list()
    for root, dirs, files in os.walk(source_code_path):
        for file in files:
            if file.endswith("bundle.json"):
                bundle_paths.append(os.path.join(root, file))
    return bundle_paths


def _gen_components_info(components_json, bundle_path, part_name):
    bundle_json = _get_json(bundle_path)
    subsystem = bundle_json["component"]["subsystem"]
    path = bundle_json["segment"]["destPath"]
    try:
        component = bundle_json["component"]["build"]["inner_kits"]
    except KeyError:
        component = bundle_json["component"]["build"]["innerapis"]
    innerapi_value_list = list()
    for i in component:
        innerapi_name = i["name"].split(':')[-1]
        if part_name == 'musl':
            innerapi_label = os.path.join("//binarys", path) + ":" + innerapi_name
        else:
            innerapi_label = os.path.join("//binarys", path, "innerapis", innerapi_name) + ":" + innerapi_name
        innerapi_value_list.append({"name": innerapi_name, "label": innerapi_label})
    if part_name == 'cjson':
        part_name = 'cJSON'
    one_component_dict = {part_name: {
        "innerapis": innerapi_value_list,
        "path": path,
        "subsystem": subsystem
    }}
    components_json.update(one_component_dict)

    return components_json


def _get_src_part_name(src_bundle_paths):
    _name = ''
    _path = ''
    for src_bundle_path in src_bundle_paths:
        src_bundle_json = _get_json(src_bundle_path)
        part_name = src_bundle_json['component']['name']
        if part_name.endswith('lite'):
            pass
        else:
            _name = part_name
            _path = src_bundle_path
    return _name, _path


def components_info_handler(part_name_list, source_code_path, hpm_cache_path, dependences_json):
    components_json = dict()
    src_bundle_paths = _get_src_bundle_path(source_code_path)
    src_part_name, src_bundle_path = _get_src_part_name(src_bundle_paths)
    components_json = _gen_components_info(components_json, src_bundle_path, src_part_name)
    for part_name in part_name_list:
        bundle_path = _get_bundle_path(hpm_cache_path, dependences_json, part_name)
        components_json = _gen_components_info(components_json, bundle_path, part_name)

    return components_json


def out_components_json(components_json, output_path):
    file_name = os.path.join(output_path, "components.json")
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(file_name, flags, modes), 'w') as f:
        json.dump(components_json, f, indent=4)


@timer
def main():
    args = get_args()

    source_code_path = args.source_code_path
    hpm_cache_path = args.hpmcache_path
    project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    output_path = os.path.join(project_path, 'out', 'build_configs', 'parts_info')
    dependences_json = get_dependence_json(hpm_cache_path)
    part_name_list = dependences_json.keys()

    components_json = components_info_handler(part_name_list, source_code_path, hpm_cache_path, dependences_json)
    out_components_json(components_json, output_path)


if __name__ == '__main__':
    main()
