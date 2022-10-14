#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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
from services.interface.preloadInterface import PreloadInterface
from resources.config import Config

from util.ioUtil import IoUtil
from util.preloader.preloader_process_data import Dirs, Outputs, Product
from util.preloader.parse_lite_subsystems_config import parse_lite_subsystem_config


class OHOSPreloader(PreloadInterface):

    def __init__(self, config: Config):
        super().__init__(config)

        self._dirs = Dirs(config)

        # preloader_output_dir
        self.preloader_output_dir = os.path.join(
            config.root_path, 'out/preloader', config.product)

        # All kinds of output files
        os.makedirs(self._dirs.preloader_output_dir, exist_ok=True)
        self._outputs = Outputs(
            self._dirs.preloader_output_dir)

        # Product & device
        self._product = Product(
            config.product, self._dirs, config.product_json)

    def __post_init__(self):

        # product parse
        self._product._do_parse()

        # get device information
        self._device = self._product._device

        # get all parts
        self._all_parts = self._product._parts

        # get build config info
        self._build_vars = self._product._build_vars

        if self._device:
            device_info = self._device.get_device_info()
            if device_info:
                if self._config.target_cpu:
                    device_info["target_cpu"] = self._config.target_cpu
                if self._config.compile_config:
                    device_info[self._config.compile_config] = True
                self._build_vars.update(device_info)

        # generate toolchain
        self._os_level = self._build_vars.get('os_level')
        self._target_os = self._build_vars.get('target_os')
        self._target_cpu = self._build_vars.get('target_cpu')
        self._toolchain_label = self._get_toolchain_label()

        # add toolchain label
        self._build_vars['product_toolchain_label'] = self._toolchain_label

        # subsystem info
        self._subsystem_info = self._get_org_subsystem_info()

    def _internel_run(self):
        self.__post_init__()

        self._generate_build_prop()
        self._generate_build_config_json()
        self._generate_parts_json()
        self._generate_parts_config_json()
        self._generate_build_gnargs_prop()
        self._generate_features_json()
        self._generate_syscap_json()
        self._generate_exclusion_modules_json()
        self._generate_platforms_build()
        self._generate_subsystem_config_json()
        self._generate_systemcapability_json()

# generate method

    # generate platforms build info to out/preloader/product_name/platforms.build
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

    # generate build gnargs prop info to out/preloader/product_name/build_gnargs.prop
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
        with open(self._outputs.build_gnargs_prop, 'w') as fobj:
            fobj.write('\n'.join(attr_list))

    # generate features to out/preloader/product_name/features.json
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

    # generate syscap to out/preloader/product_name/syscap.json
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

    # generate exclusion modules info to out/preloader/product_name/exclusion_modules.json
    def _generate_exclusion_modules_json(self):
        exclusions = {}
        for _part_name, vals in self._all_parts.items():
            _exclusions = vals.get('exclusions')
            if _exclusions:
                pair = dict()
                pair[_part_name] = _exclusions
                exclusions.update(pair)
        IoUtil.dump_json_file(self._outputs.exclusion_modules_json, exclusions)

    # generate build config info to out/preloader/product_name/build_config.json
    def _generate_build_config_json(self):
        IoUtil.dump_json_file(
            self._outputs.build_config_json, self._build_vars)

    # generate build prop info to out/preloader/product_name/build.prop
    def _generate_build_prop(self):
        build_vars_list = []
        for k, v in self._build_vars.items():
            build_vars_list.append('{}={}'.format(k, v))
        with open(self._outputs.build_prop, 'w') as fobj:
            fobj.write('\n'.join(build_vars_list))

    # generate parts to out/preloader/product_name/parts.json
    def _generate_parts_json(self):
        parts_info = {"parts": sorted(list(self._all_parts.keys()))}
        IoUtil.dump_json_file(self._outputs.parts_json, parts_info)

    # generate parts config to out/preloader/product_name/parts_config.json
    def _generate_parts_config_json(self):
        parts_config = {}
        for part in self._all_parts:
            part = part.replace(":", "_")
            part = part.replace("-", "_")
            part = part.replace(".", "_")
            part = part.replace("/", "_")
            parts_config[part] = True
        IoUtil.dump_json_file(self._outputs.parts_config_json, parts_config)

    # generate subsystem config info to out/preloader/product_name/subsystem_config.json
    def _generate_subsystem_config_json(self):
        if self._subsystem_info:
            self._subsystem_info.update(
                self._product._get_product_specific_subsystem())
            self._subsystem_info.update(
                self._device.get_device_specific_subsystem())
        IoUtil.dump_json_file(
            self._outputs.subsystem_config_json, self._subsystem_info)

    # generate systemcapability_json to out/preloader/product_name/systemcapability.json
    def _generate_systemcapability_json(self):
        IoUtil.dump_json_file(
            self._outputs.systemcapability_json, self._product._syscap_info)

# get method

    def _get_org_subsystem_info(self):
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

    def _get_toolchain_label(self):
        if self._os_level == 'mini' or self._os_level == 'small':
            toolchain_label = ""
        else:
            toolchain_label = '//build/toolchain/{0}:{0}_clang_{1}'.format(
                self._target_os, self._target_cpu)
        return toolchain_label
