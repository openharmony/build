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

from resources.global_var import CURRENT_OHOS_ROOT
from exceptions.ohos_exception import OHOSException
from util.io_util import IoUtil
from containers.status import throw_exception


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


def _recurrent_search_bundle_file(path: str):
    cur_dir = path
    while cur_dir != CURRENT_OHOS_ROOT:
        bundle_json = os.path.join(
            cur_dir, 'bundle.json')
        if os.path.exists(bundle_json):
            return True, bundle_json
        cur_dir = os.path.dirname(cur_dir)
    return False, ''
