#!/usr/bin/env python3
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

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util import file_utils  # noqa: E402


class BundlePartObj(object):
    def __init__(self, bundle_config_file, exclusion_modules_config_file, load_test_config):
        self._build_config_file = bundle_config_file
        self._exclusion_modules_config_file = exclusion_modules_config_file
        self._load_test_config = load_test_config
        self._loading_config()

    def _loading_config(self):
        if not os.path.exists(self._build_config_file):
            raise Exception("file '{}' doesn't exist.".format(
                self._build_config_file))
        self.bundle_info = file_utils.read_json_file(self._build_config_file)
        if self.bundle_info is None:
            raise Exception("read file '{}' failed.".format(
                self._build_config_file))
        self._check_format()
        self.exclusion_modules_info = file_utils.read_json_file(
            self._exclusion_modules_config_file)

    def _check_format(self):
        _tip_info = "bundle.json info is incorrect in '{}'".format(
            self._build_config_file)
        if 'component' not in self.bundle_info:
            raise Exception("{}, 'component' is required.".format(_tip_info))
        _component_info = self.bundle_info.get('component')
        if 'name' not in _component_info:
            raise Exception(
                "{}, 'component.name' is required.".format(_tip_info))
        if 'subsystem' not in _component_info:
            raise Exception(
                "{}, 'component.subsystem' is required.".format(_tip_info))
        if 'build' not in _component_info:
            raise Exception(
                "{}, 'component.build' is required.".format(_tip_info))
        _bundle_build = _component_info.get('build')
        if 'sub_component' not in _bundle_build and 'group_type' not in _bundle_build \
            and 'modules' not in _bundle_build:
            raise Exception(
                "{}, 'component.build.sub_component','component.build.group_type' or \
                'component.build.modules' is required.".format(_tip_info))
        if 'group_type' in _bundle_build:
            group_list = ['base_group', 'fwk_group', 'service_group']
            _module_groups = _bundle_build.get('group_type')
            for _group_type, _module_list in _module_groups.items():
                if _group_type not in group_list:
                    raise Exception("{}, incorrect group type".format(_tip_info))

    def to_ohos_build(self):
        _component_info = self.bundle_info.get('component')
        _subsystem_name = _component_info.get('subsystem')
        _part_name = _component_info.get('name')
        _bundle_build = _component_info.get('build')
        _exclusion_modules_info = self.exclusion_modules_info
        _ohos_build_info = {}
        _ohos_build_info['subsystem'] = _subsystem_name
        _part_info = {}
        module_list = []
        if _component_info.get('build').__contains__('sub_component'):
            _part_info['module_list'] = _component_info.get('build').get(
                'sub_component')
        elif _component_info.get('build').__contains__('modules'):
            _part_info['module_list'] = _component_info.get('build').get('modules')
        elif _component_info.get('build').__contains__('group_type'):
            _module_groups = _component_info.get('build').get('group_type')
            for _group_type, _module_list in _module_groups.items():
                _key = '{}:{}'.format(_subsystem_name, _part_name)
                if not _exclusion_modules_info.get(_key):
                    module_list.extend(_module_list)
                elif _group_type not in _exclusion_modules_info.get(_key):
                    module_list.extend(_module_list)
            _part_info['module_list'] = module_list
        if 'inner_kits' in _bundle_build:
            _part_info['inner_kits'] = _bundle_build.get('inner_kits')
        elif 'inner_api' in _bundle_build:
            _part_info['inner_kits'] = _bundle_build.get('inner_api')
        if 'test' in _bundle_build and self._load_test_config:
            _part_info['test_list'] = _bundle_build.get('test')
        if 'features' in _component_info:
            _part_info['feature_list'] = _component_info.get('features')
        if 'syscap' in _component_info:
            _part_info['system_capabilities'] = _component_info.get('syscap')
        if 'hisysevent_config' in _component_info:
            _part_info['hisysevent_config'] = _component_info.get('hisysevent_config')
        _ohos_build_info['parts'] = {_part_name: _part_info}
        return _ohos_build_info
