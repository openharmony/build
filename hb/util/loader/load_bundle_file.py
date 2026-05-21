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

import sys
import os
import copy
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from resources.config import Config
from util.io_util import IoUtil
from util.log_util import LogUtil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util import file_utils  # noqa: E402


class BundlePartObj(object):
    def __init__(self, bundle_config_file, exclusion_modules_config_file,
                 dependency_pruning_config_file, load_test_config):
        self._build_config_file = bundle_config_file
        self._exclusion_modules_config_file = exclusion_modules_config_file
        self._dependency_pruning_config_file = dependency_pruning_config_file
        self._load_test_config = load_test_config
        self._condition_context = self._build_condition_context()
        self._matched_condition_keys = set()
        self._loading_config()

    def _build_condition_context(self):
        config_info = {}
        try:
            config_info = IoUtil.read_json_file(Config().config_json)
        except Exception:
            config_info = {}

        config = Config()
        context = dict(config_info)
        for key in (
                'compile_mode', 'target_os', 'target_cpu', 'os_level',
                'product', 'board', 'device_path', 'product_path'):
            value = getattr(config, key, None)
            if value is not None:
                context[key] = value

        context['is_host_product'] = context.get('compile_mode') == 'host'
        return context

    @throw_exception
    def _loading_config(self):
        if not os.path.exists(self._build_config_file):
            raise OHOSException("file '{}' doesn't exist.".format(
                self._build_config_file), "2011")
        self.bundle_info = file_utils.read_json_file(self._build_config_file)
        if self.bundle_info is None:
            raise OHOSException("read file '{}' failed.".format(
                self._build_config_file), "2011")
        self._check_format()
        self.exclusion_modules_info = file_utils.read_json_file(
            self._exclusion_modules_config_file)
        self.dependency_pruning_info = file_utils.read_json_file(
            self._dependency_pruning_config_file)

    def _apply_dependency_pruning(self, subsystem_name, part_name, part_deps):
        if not part_deps or not self.dependency_pruning_info:
            return part_deps

        pruning_rule = self.dependency_pruning_info.get(
            f'{subsystem_name}:{part_name}')
        if not pruning_rule:
            return part_deps

        pruned_part_deps = copy.deepcopy(part_deps)
        for dep_group in ('components', 'third_party'):
            pruned_names = pruning_rule.get(dep_group, [])
            if not pruned_names or dep_group not in pruned_part_deps:
                continue
            pruned_part_deps[dep_group] = [
                dep_name for dep_name in pruned_part_deps.get(dep_group, [])
                if dep_name not in pruned_names
            ]
        return pruned_part_deps

    def _get_pruning_rule(self, subsystem_name, part_name):
        if not self.dependency_pruning_info:
            return {}
        return self.dependency_pruning_info.get(
            f'{subsystem_name}:{part_name}', {})

    def _apply_module_pruning(self, module_list, pruning_names):
        if not module_list or not pruning_names:
            return module_list
        return [
            module_name for module_name in module_list
            if module_name not in pruning_names
        ]

    def _get_conditions(self, bundle_build):
        conditions = bundle_build.get('conditions')
        if conditions is None:
            return {}
        if not isinstance(conditions, dict):
            LogUtil.hb_warning(
                "ignore invalid 'component.build.conditions' in '{}'".format(
                    self._build_config_file))
            return {}
        return conditions

    def _match_conditions(self, item_key, condition_expr):
        if not isinstance(condition_expr, dict):
            LogUtil.hb_warning(
                "ignore invalid condition for '{}' in '{}'".format(
                    item_key, self._build_config_file))
            return False

        for attr_name, expected_value in condition_expr.items():
            if attr_name not in self._condition_context:
                LogUtil.hb_warning(
                    "condition attribute '{}' for '{}' in '{}' "
                    "is undefined in current build context".format(
                        attr_name, item_key, self._build_config_file))
                return False

            actual_value = self._condition_context.get(attr_name)
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif actual_value != expected_value:
                return False
        return True

    def _apply_conditions(self, items, key_getter):
        if not items:
            return items

        bundle_build = self.bundle_info.get('component', {}).get('build', {})
        conditions = self._get_conditions(bundle_build)
        if not conditions:
            return items

        filtered_items = []
        seen_keys = set()
        for item in items:
            item_key = key_getter(item)
            seen_keys.add(item_key)
            condition_expr = conditions.get(item_key)
            if condition_expr is None:
                filtered_items.append(item)
                continue
            self._matched_condition_keys.add(item_key)
            if self._match_conditions(item_key, condition_expr):
                filtered_items.append(item)
        return filtered_items

    @throw_exception
    def _check_format(self):
        _tip_info = "bundle.json info is incorrect in '{}'".format(
            self._build_config_file)
        if 'component' not in self.bundle_info:
            raise OHOSException(
                "{}, 'component' is required.".format(_tip_info), "2011")
        _component_info = self.bundle_info.get('component')
        if 'name' not in _component_info:
            raise OHOSException(
                "{}, 'component.name' is required.".format(_tip_info), "2011")
        if 'subsystem' not in _component_info:
            raise OHOSException(
                "{}, 'component.subsystem' is required.".format(_tip_info), "2011")
        if 'build' not in _component_info:
            raise OHOSException(
                "{}, 'component.build' is required.".format(_tip_info), "2011")
        _bundle_build = _component_info.get('build')
        if 'sub_component' not in _bundle_build and 'group_type' not in _bundle_build \
                and 'modules' not in _bundle_build:
            raise OHOSException(
                "{}, 'component.build.sub_component','component.build.group_type' or \
                'component.build.modules' is required.".format(_tip_info), "2011")
        if 'group_type' in _bundle_build:
            group_list = ['base_group', 'fwk_group', 'service_group']
            _module_groups = _bundle_build.get('group_type')
            for _group_type, _module_list in _module_groups.items():
                if _group_type not in group_list:
                    raise OHOSException(
                        "{}, incorrect group type".format(_tip_info), "2011")

    def to_ohos_build(self):
        _component_info = self.bundle_info.get('component')
        _subsystem_name = _component_info.get('subsystem')
        _part_name = _component_info.get('name')
        _bundle_build = _component_info.get('build')
        _exclusion_modules_info = self.exclusion_modules_info
        _pruning_rule = self._get_pruning_rule(_subsystem_name, _part_name)
        _ohos_build_info = {}
        _ohos_build_info['subsystem'] = _subsystem_name
        _part_info = {}
        module_list = []
        if _component_info.get('build').__contains__('sub_component'):
            sub_component_list = self._apply_conditions(
                _component_info.get('build').get('sub_component'),
                lambda item: item)
            _part_info['module_list'] = self._apply_module_pruning(
                sub_component_list,
                _pruning_rule.get('sub_component', []))
        elif _component_info.get('build').__contains__('modules'):
            modules_list = self._apply_conditions(
                _component_info.get('build').get('modules'),
                lambda item: item)
            _part_info['module_list'] = self._apply_module_pruning(
                modules_list,
                _pruning_rule.get('modules', []))
        elif _component_info.get('build').__contains__('group_type'):
            _module_groups = _component_info.get('build').get('group_type')
            for _group_type, _module_list in _module_groups.items():
                _key = '{}:{}'.format(_subsystem_name, _part_name)
                filtered_group_modules = self._apply_conditions(
                    _module_list, lambda item: item)
                if not _exclusion_modules_info.get(_key):
                    module_list.extend(filtered_group_modules)
                elif _group_type not in _exclusion_modules_info.get(_key):
                    module_list.extend(filtered_group_modules)
            _part_info['module_list'] = self._apply_module_pruning(
                module_list, _pruning_rule.get('group_type', []))
        if 'inner_kits' in _bundle_build:
            inner_kits = self._apply_conditions(
                _bundle_build.get('inner_kits'),
                lambda item: item.get('name'))
            if inner_kits:
                _part_info['inner_kits'] = inner_kits
        elif 'inner_api' in _bundle_build:
            inner_api = self._apply_conditions(
                _bundle_build.get('inner_api'),
                lambda item: item.get('name'))
            if inner_api:
                _part_info['inner_kits'] = inner_api
        if 'test' in _bundle_build and self._load_test_config:
            test_list = self._apply_conditions(
                _bundle_build.get('test'), lambda item: item)
            if test_list:
                _part_info['test_list'] = test_list
        if 'features' in _component_info:
            _part_info['feature_list'] = _component_info.get('features')
        if 'syscap' in _component_info:
            _part_info['system_capabilities'] = _component_info.get('syscap')
        if 'hisysevent_config' in _component_info:
            _part_info['hisysevent_config'] = _component_info.get(
                'hisysevent_config')
        _part_info['part_deps'] = self._apply_dependency_pruning(
            _subsystem_name, _part_name, _component_info.get('deps', {}))
        _part_info['part_deps']['build_config_file'] = self._build_config_file

        conditions = self._get_conditions(_bundle_build)
        for item_key in conditions.keys():
            if item_key not in self._matched_condition_keys:
                LogUtil.hb_warning(
                    "condition target '{}' in '{}' does not exist in "
                    "'sub_component', 'modules', 'group_type', 'inner_kits', "
                    "'inner_api' or 'test'".format(
                        item_key, self._build_config_file))

        _ohos_build_info['parts'] = {_part_name: _part_info}
        return _ohos_build_info
