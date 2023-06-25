#!/usr/bin/env python3
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
import stat

from services.interface.preload_interface import PreloadInterface
from util.io_util import IoUtil
from util.preloader.preloader_process_data import Dirs, Outputs, Product
from util.preloader.parse_lite_subsystems_config import parse_lite_subsystem_config
from util.log_util import LogUtil


class OHOSPreloader(PreloadInterface):

    def __init__(self):
        super().__init__()
        self._dirs = ""
        self._outputs = ""
        self._product = ""
        self._os_level = ""
        self._target_cpu = ""
        self._target_os = ""
        self._toolchain_label = ""
        self._subsystem_info = {}
        self._all_parts = {}
        self._build_vars = {}
        self._compile_standard_whitelist_info = {}

    def __post_init__(self):
        self._dirs = Dirs(self._config)
        self._outputs = Outputs(self._dirs.preloader_output_dir)
        self._product = Product(self._dirs, self._config)
        self._all_parts = self._product._parts
        self._build_vars = self._product._build_vars
        self._os_level = self._build_vars.get('os_level')
        self._target_os = self._build_vars.get('target_os')
        self._target_cpu = self._build_vars.get('target_cpu')
        self._toolchain_label = self._build_vars.get('product_toolchain_label')
        self._subsystem_info = self._get_org_subsystem_info()
        self._compile_standard_whitelist_info = self._get_compile_standard_whitelist_info()

# generate method

    '''Description: generate platforms build info to "out/preloader/{product_name}/platforms.build"
    @parameter:none
    @return :none
    '''

    def _generate_platforms_build(self):
        config = {
            'target_os': self._target_os,
            "target_cpu": self._target_cpu,
            "toolchain": self._toolchain_label,
            "parts_config": os.path.relpath(self._outputs.parts_json,
                                            self._dirs.preloader_output_dir)
        }
        platform_config = {'version': 2, 'platforms': {'phone': config}}
        IoUtil.dump_json_file(self._outputs.platforms_build, platform_config)
        LogUtil.hb_info(
            'generated platforms build info to {}/platforms.build'.format(self._dirs.preloader_output_dir))

    '''Description: generate build gnargs prop info to "out/preloader/{product_name}/build_gnargs.prop"
    @parameter:none
    @return :none
    '''

    def _generate_build_gnargs_prop(self):
        all_features = {}
        for _part_name, vals in self._all_parts.items():
            _features = vals.get('features')
            if _features:
                all_features.update(_features)
        attr_list = []
        for key, val in all_features.items():
            _item = ''
            if isinstance(val, bool):
                _item = f'{key}={str(val).lower()}'
            elif isinstance(val, int):
                _item = f'{key}={val}'
            elif isinstance(val, str):
                _item = f'{key}="{val}"'
            else:
                raise Exception("part feature '{key}:{val}' type not support.")
            attr_list.append(_item)
        with os.fdopen(os.open(self._outputs.build_gnargs_prop,
                               os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fobj:
            fobj.write('\n'.join(attr_list))
        LogUtil.hb_info(
            'generated build gnargs prop info to {}/build_gnargs.prop'.format(self._dirs.preloader_output_dir))

    '''Description: generate features to "out/preloader/{product_name}/features.json"
    @parameter:none
    @return :none
    '''

    def _generate_features_json(self):
        all_features = {}
        part_feature_map = {}
        for _part_name, vals in self._all_parts.items():
            _features = vals.get('features')
            if _features:
                all_features.update(_features)
            if _features:
                part_feature_map[_part_name.split(
                    ':')[1]] = list(_features.keys())
        parts_feature_info = {
            "features": all_features,
            "part_to_feature": part_feature_map
        }
        IoUtil.dump_json_file(self._outputs.features_json, parts_feature_info)
        LogUtil.hb_info(
            'generated features info to {}/features.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate syscap to "out/preloader/product_name/syscap.json"
    @parameter:none
    @return :none
    '''

    def _generate_syscap_json(self):
        all_syscap = {}
        part_syscap_map = {}
        for _part_name, vals in self._all_parts.items():
            _syscap = vals.get('syscap')
            if _syscap:
                all_syscap.update(_syscap)
                part_syscap_map[_part_name.split(':')[1]] = _syscap
        parts_syscap_info = {
            "syscap": all_syscap,
            "part_to_syscap": part_syscap_map
        }
        IoUtil.dump_json_file(self._outputs.syscap_json, parts_syscap_info)
        LogUtil.hb_info(
            'generated syscap info to {}/syscap.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate exclusion modules info to "out/preloader/product_name/exclusion_modules.json"
    @parameter:none
    @return :none
    '''

    def _generate_exclusion_modules_json(self):
        exclusions = {}
        for _part_name, vals in self._all_parts.items():
            _exclusions = vals.get('exclusions')
            if _exclusions:
                pair = dict()
                pair[_part_name] = _exclusions
                exclusions.update(pair)
        IoUtil.dump_json_file(self._outputs.exclusion_modules_json, exclusions)
        LogUtil.hb_info(
            'generated exclusion modules info to {}/exclusion_modules.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate build config info to "out/preloader/product_name/build_config.json"
    @parameter:none
    @return :none
    '''

    def _generate_build_config_json(self):
        IoUtil.dump_json_file(
            self._outputs.build_config_json, self._build_vars)
        LogUtil.hb_info(
            'generated build config info to {}/build_config.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate build prop info to "out/preloader/product_name/build.prop"
    @parameter:none
    @return :none
    '''

    def _generate_build_prop(self):
        build_vars_list = []
        for key, value in self._build_vars.items():
            build_vars_list.append('{}={}'.format(key, value))
        with os.fdopen(os.open(self._outputs.build_prop,
                               os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), 'w') as fobj:
            fobj.write('\n'.join(build_vars_list))
        LogUtil.hb_info(
            'generated build prop info to {}/build.prop'.format(self._dirs.preloader_output_dir))

    '''Description: generate parts to "out/preloader/product_name/parts.json"
    @parameter:none
    @return :none
    '''

    def _generate_parts_json(self):
        parts_info = {"parts": sorted(list(self._all_parts.keys()))}
        IoUtil.dump_json_file(self._outputs.parts_json, parts_info)
        LogUtil.hb_info(
            'generated product parts info to {}/parts.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate parts config to "out/preloader/product_name/parts_config.json"
    @parameter:none
    @return :none
    '''

    def _generate_parts_config_json(self):
        parts_config = {}
        for part in self._all_parts:
            part = part.replace(":", "_")
            part = part.replace("-", "_")
            part = part.replace(".", "_")
            part = part.replace("/", "_")
            parts_config[part] = True
        IoUtil.dump_json_file(self._outputs.parts_config_json, parts_config)
        LogUtil.hb_info(
            'generated parts config info to {}/parts_config.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate subsystem config info to "out/preloader/product_name/subsystem_config.json"
    @parameter:none
    @return :none
    '''

    def _generate_subsystem_config_json(self):
        if self._subsystem_info:
            self._subsystem_info.update(
                self._product._get_product_specific_subsystem())
            self._subsystem_info.update(
                self._product._get_device_specific_subsystem())
        IoUtil.dump_json_file(
            self._outputs.subsystem_config_json, self._subsystem_info)
        LogUtil.hb_info(
            'generated subsystem config info to {}/subsystem_config.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate systemcapability_json to "out/preloader/product_name/systemcapability.json"
    @parameter:none
    @return :none
    '''

    def _generate_systemcapability_json(self):
        IoUtil.dump_json_file(
            self._outputs.systemcapability_json, self._product._syscap_info)
        LogUtil.hb_info(
            'generated system capability info to {}/systemcapability.json'.format(self._dirs.preloader_output_dir))

    '''Description: generate compile_standard_whitelist info  to "out/preloader/product_name/compile_standard_whitelist.json"
    @parameter:none
    @return :none
    '''

    def _generate_compile_standard_whitelist_json(self):
        IoUtil.dump_json_file(
            self._outputs.compile_standard_whitelist_json, self._compile_standard_whitelist_info)
        LogUtil.hb_info(
            'generated compile_standard_whitelist info to {}/compile_standard_whitelist.json'
            .format(self._dirs.preloader_output_dir))

# get method

    def _get_org_subsystem_info(self) -> dict:
        subsystem_info = {}
        if self._os_level == "standard":
            subsystem_info = IoUtil.read_json_file(
                self._dirs.subsystem_config_json)
        elif self._os_level == "mini" or self._os_level == "small":
            ohos_build_output_dir = os.path.join(self._dirs.preloader_output_dir,
                                                 '{}_system'.format(self._os_level))
            subsystem_info = parse_lite_subsystem_config(
                self._dirs.lite_components_dir, ohos_build_output_dir,
                self._dirs.source_root_dir, self._dirs.subsystem_config_json)
        return subsystem_info

    def _get_compile_standard_whitelist_info(self) -> dict:
        allow_info_file = "out/products_ext/{}/compile_standard_whitelist.json".format(self.config.product)
        allow_info_file = os.path.join(self._dirs.source_root_dir, allow_info_file)
        if not os.path.exists(allow_info_file):
            allow_info_file = os.path.join(self._dirs.source_root_dir, "build/compile_standard_whitelist.json")
        
        allow_info = IoUtil.read_json_file(allow_info_file)
        return allow_info
