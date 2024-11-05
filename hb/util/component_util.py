#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
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

import os
import re
import sys

from resources.global_var import CURRENT_OHOS_ROOT
from resources.global_var import COMPONENTS_PATH_DIR
from exceptions.ohos_exception import OHOSException
from util.io_util import IoUtil
from containers.status import throw_exception


def get_part_name():
    part_name_list = []
    if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):
        for name in sys.argv[2:]:
            if not name.startswith('-'):
                part_name_list.append(name)
            else:
                break
    return part_name_list


class ComponentUtil():

    @staticmethod
    def is_in_component_dir(path: str) -> bool:
        return _recurrent_search_bundle_file(path)[0]

    @staticmethod
    def is_component_in_product(component_name: str, product_name: str) -> bool:
        build_configs_path = os.path.join(
            CURRENT_OHOS_ROOT, 'out', product_name, 'build_configs')
        if os.path.exists(build_configs_path):
            for root, dirs, files in os.walk(build_configs_path, topdown=True, followlinks=False):
                if component_name in dirs:
                    return True
        return False

    @staticmethod
    def get_component_name(path: str) -> str:
        found_bundle_file, bundle_path = _recurrent_search_bundle_file(path)
        if found_bundle_file:
            data = IoUtil.read_json_file(bundle_path)
            return data['component']['name']

        return ''

    @staticmethod
    def get_component(path: str) -> str:
        found_bundle_file, bundle_path = _recurrent_search_bundle_file(path)
        if found_bundle_file:
            data = IoUtil.read_json_file(bundle_path)
            return data['component']['name'], os.path.dirname(bundle_path)

        return '', ''

    @staticmethod
    def get_default_deps(variant: str) -> str:
        gen_default_deps_json(variant, CURRENT_OHOS_ROOT)
        default_deps_path = os.path.join(
            CURRENT_OHOS_ROOT, 'out', 'preloader', 'default_deps.json')
        return default_deps_path

    @staticmethod
    @throw_exception
    def get_component_module_full_name(out_path: str, component_name: str, module_name: str) -> str:
        root_path = os.path.join(out_path, "build_configs")
        target_info = ""
        module_list = []
        for file in os.listdir(root_path):
            if len(target_info):
                break
            file_path = os.path.join(root_path, file)
            if not os.path.isdir(file_path):
                continue
            for component in os.listdir(file_path):
                if os.path.isdir(os.path.join(file_path, component)) and component == component_name:
                    target_info = IoUtil.read_file(
                        os.path.join(file_path, component, "BUILD.gn"))
                    break
        pattern = re.compile(r'(?<=module_list = )\[([^\[\]]*)\]')
        results = pattern.findall(target_info)
        for each_tuple in results:
            module_list = each_tuple.replace('\n', '').replace(
                ' ', '').replace('\"', '').split(',')
        for target_path in module_list:
            if target_path != '':
                path, target = target_path.split(":")
                if target == module_name:
                    return target_path

        raise OHOSException('You are trying to compile a module {} which do not exists in {} while compiling {}'.format(
            module_name, component_name, out_path), "4001")

    @staticmethod
    def search_bundle_file(component_name: str):
        all_bundle_path = get_all_bundle_path(CURRENT_OHOS_ROOT)
        return all_bundle_path.get(component_name)


def _recurrent_search_bundle_file(path: str):
    cur_dir = path
    while cur_dir != CURRENT_OHOS_ROOT:
        bundle_json = os.path.join(
            cur_dir, 'bundle.json')
        if os.path.exists(bundle_json):
            return True, bundle_json
        cur_dir = os.path.dirname(cur_dir)
    return False, ''


def get_all_bundle_path(path):
    bundles_path = {}
    for root, dirnames, filenames in os.walk(path):
        if root == os.path.join(path, "out") or root == os.path.join(path, ".repo"):
            continue
        for filename in filenames:
            if filename == "bundle.json":
                bundle_json = os.path.join(root, filename)
                data = IoUtil.read_json_file(bundle_json)
                bundles_path = process_bundle_path(bundle_json, bundles_path, data)
    IoUtil.dump_json_file(COMPONENTS_PATH_DIR, bundles_path)
    return bundles_path


def process_bundle_path(bundle_json, bundles_path, data):
    if data.get("component") and data.get("component").get("name"):
        bundles_path[data["component"]["name"]] = os.path.dirname(bundle_json)
    return bundles_path


def gen_default_deps_json(variant, root_path):
    part_name_list = get_part_name()
    default_deps_out_file = os.path.join(root_path, "out", "preloader", "default_deps.json")
    default_deps_file = os.path.join(root_path, "build", "indep_configs", "variants", "common", 'default_deps.json')
    default_deps_json = IoUtil.read_json_file(default_deps_file)
    default_deps_json.append("variants_" + variant)

    part_white_list_path = os.path.join(root_path, "build", "indep_configs", "config",
                                        "rust_download_part_whitelist.json")
    part_white_list = IoUtil.read_json_file(part_white_list_path)
    for part_name in part_name_list:
        if part_name in part_white_list and 'rust' not in default_deps_json:
            default_deps_json.append('rust')

    preloader_path = os.path.join(root_path, "out", "preloader")
    os.makedirs(preloader_path, exist_ok=True)
    IoUtil.dump_json_file(default_deps_out_file, default_deps_json)
