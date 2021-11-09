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
import sys
import argparse
from dataclasses import dataclass

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file, write_file  # noqa: E402, E501
from loader.preloader.parse_lite_product_config import get_lite_parts_list  # noqa: E402, E501
from loader.preloader.parse_lite_subsystems_config import parse_lite_subsystem_config  # noqa: E402, E501


def _get_product_config(config_dir, product_name):
    config_file = os.path.join(config_dir, '{}.json'.format(product_name))
    if not os.path.exists(config_file):
        raise Exception(
            "product configuration '{}' doesn't exist.".format(config_file))
    return config_file


def _get_base_parts(base_config_dir, os_level):
    system_base_config_file = os.path.join(base_config_dir,
                                           '{}_system.json'.format(os_level))
    if not os.path.exists(system_base_config_file):
        raise Exception("product configuration '{}' doesn't exist.".format(
            system_base_config_file))
    data = read_json_file(system_base_config_file)
    if data is None:
        raise Exception(
            "read file '{}' failed.".format(system_base_config_file))
    return data


def _get_inherit_parts(config_info, product_config_dir):
    inherit_config = config_info.get('inherit')
    inherit_parts = {}
    if inherit_config:
        for _config in inherit_config:
            _file = os.path.join(product_config_dir, _config)
            _info = read_json_file(_file)
            if _info is None:
                raise Exception("read file '{}' failed.".format(_file))
            if _info.get('parts'):
                inherit_parts.update(_info.get('parts'))
    return inherit_parts


def _get_device_info(device_name, device_config_path):
    device_config_file = os.path.join(device_config_path,
                                      '{}.json'.format(device_name))
    device_info = read_json_file(device_config_file)
    if device_info and device_info.get('device_name') != device_name:
        raise Exception("device name configuration incorrect in '{}'".format(
            device_config_file))
    return device_info


def _output_platforms_config(target_os, target_cpu, toolchain_label,
                             parts_config_file, output_file):
    config = {
        'target_os': target_os,
        "target_cpu": target_cpu,
        "toolchain": toolchain_label,
        "parts_config": parts_config_file
    }

    platform_config_info = {'version': 2, 'platforms': {'phone': config}}
    write_json_file(output_file, platform_config_info)


def _output_gnargs_prop(all_features, output_file):
    features_list = _part_features_to_list(all_features)
    write_file(output_file, '\n'.join(features_list))


def _get_org_subsytem_info(subsystem_config_file, os_level, configs):
    subsystem_info = {}
    if os_level == "standard":
        subsystem_info = read_json_file(subsystem_config_file)
    elif os_level == "mini" or os_level == "small":
        ohos_build_output_dir = os.path.join(configs.preloader_output_dir,
                                             '{}_system'.format(os_level))
        subsystem_info = parse_lite_subsystem_config(
            configs.lite_components_dir, ohos_build_output_dir,
            configs.source_root_dir)
    return subsystem_info


def _merge_subsystem_config(product, device, configs, os_level, output_file):
    subsystem_info = _get_org_subsytem_info(configs.subsystem_config_json,
                                            os_level, configs)
    if subsystem_info:
        subsystem_info.update(product.get_product_specific_subsystem())
        subsystem_info.update(device.get_device_specific_subsystem())
    write_json_file(output_file, subsystem_info)


def _output_parts_features(all_parts, output_file):
    all_features = {}
    part_feature_map = {}
    for _part_name, vals in all_parts.items():
        _features = vals.get('features')
        if _features:
            all_features.update(_features)
        if _features:
            part_feature_map[_part_name.split(':')[1]] = list(_features.keys())
    parts_feature_info = {
        "features": all_features,
        "part_to_feature": part_feature_map
    }
    write_json_file(output_file, parts_feature_info)
    return all_features


def _part_features_to_list(all_part_features):
    attr_list = []
    for key, val in all_part_features.items():
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
    return attr_list


def _output_build_vars(build_vars, build_prop, build_config_json):
    build_vars_list = []
    for k, v in build_vars.items():
        build_vars_list.append('{}={}'.format(k, v))
    write_file(build_prop, '\n'.join(build_vars_list))
    write_json_file(build_config_json, build_vars)


def _output_parts_json(all_parts, output_file):
    parts_info = {"parts": sorted(list(all_parts.keys()))}
    write_json_file(output_file, parts_info)


class Product():
    def __init__(self, product_name, configs):
        self._name = product_name
        self._configs = configs
        self._config_file = _get_product_config(
            self._configs.product_config_dir, product_name)
        self._config_info = read_json_file(self._config_file)

        if self._config_info:
            device_name = self._config_info.get('product_device')
            self._device = Device(device_name, configs)
        else:
            self._device = None

        self._device_info = _get_device_info(self._name,
                                             self._configs.device_config_dir)

    def get_product_name(self):
        return self._name

    def get_product_build_path(self):
        if self._config_info:
            return self._config_info.get('product_build_path')
        else:
            return None

    def get_device(self):
        return self._device

    def _get_product_specific_parts(self):
        part_name = 'product_{}'.format(self._name)
        subsystem_name = part_name
        info = {}
        info['{}:{}'.format(subsystem_name, part_name)] = {}
        return info

    def get_product_specific_subsystem(self):
        info = {}
        subsystem_name = 'product_{}'.format(self._name)
        if self.get_product_build_path():
            info[subsystem_name] = {
                'name': subsystem_name,
                'path': self.get_product_build_path()
            }
        return info

    def _parse_config_v2(self, config_info):
        os_level = config_info.get("type")
        if os_level not in ['standard', 'large', 'mini', 'small']:
            raise Exception("product config incorrect.")

        # 1. inherit parts infomation from base config
        all_parts = _get_base_parts(self._configs.base_parts_config_dir,
                                    os_level)
        # 2. inherit parts information from inherit config
        all_parts.update(
            _get_inherit_parts(config_info, self._configs.product_config_dir))

        product_name = config_info.get('product_name')
        product_company = config_info.get('product_company')

        # 3. get parts information from product config
        if os_level == 'mini' or os_level == 'small':
            all_parts.update(
                get_lite_parts_list(self._configs.lite_config_dir,
                                    product_name, product_company))
            all_parts.update(self._get_product_specific_parts())
            if self._device:
                all_parts.update(self._device.get_device_specific_parts())

        else:
            current_product_parts = config_info.get("parts")
            if current_product_parts:
                all_parts.update(current_product_parts)

        build_vars = {}
        build_vars['os_level'] = os_level
        build_vars['product_name'] = product_name
        build_vars['product_company'] = product_company
        if self._config_info:
            build_vars['device_name'] = self._config_info.get('product_device')
        return all_parts, build_vars

    def _parse_config_v1(self):
        build_vars = {"os_level": 'large'}
        return {}, build_vars

    def parse_config(self):
        config_version = None
        if self._config_info:
            config_version = self._config_info.get('version')
        if not config_version:
            config_version = "1.0"
        if config_version == "2.0":
            if self._config_info and self._name != self._config_info.get(
                    'product_name'):
                raise Exception(
                    "product name configuration incorrect in '{}'".format(
                        self._config_file))
            return self._parse_config_v2(self._config_info)
        else:
            return self._parse_config_v1()


class Device():
    def __init__(self, device_name, configs):
        self._name = device_name
        self._configs = configs
        self._device_info = _get_device_info(self._name,
                                             self._configs.device_config_dir)

    def get_device_info(self):
        return self._device_info

    def get_device_build_path(self):
        if self._device_info:
            return self._device_info.get('device_build_path')
        else:
            return None

    def get_device_name(self):
        return self._name

    def get_device_specific_parts(self):
        info = {}
        if self._device_info:
            device_build_path = self._device_info.get('device_build_path')
            if device_build_path:
                subsystem_name = 'device_{}'.format(self._name)
                part_name = subsystem_name
                info['{}:{}'.format(subsystem_name, part_name)] = {}
        return info

    def get_device_specific_subsystem(self):
        info = {}
        subsystem_name = 'device_{}'.format(self._name)
        if self.get_device_build_path():
            info[subsystem_name] = {
                'name': subsystem_name,
                'path': self.get_device_build_path()
            }
        return info


@dataclass
class Configs:
    def __init__(self, args):
        self.__post_init__(args)

    def __post_init__(self, args):
        self.source_root_dir = args.source_root_dir
        self.product_config_dir = args.product_config_dir
        self.preloader_output_dir = args.preloader_output_dir
        self.lite_config_dir = args.lite_product_config_dir
        self.lite_components_dir = args.lite_components_dir
        self.productdefine_dir = args.productdefine_dir
        self.subsystem_config_json = args.subsystem_config_file
        if args.device_config_dir:
            self.device_config_dir = args.device_config_dir
        else:
            self.device_config_dir = os.path.join(self.productdefine_dir,
                                                  'device')
        if args.base_parts_config_dir:
            self.base_parts_configs = args.base_parts_config_dir
        else:
            self.base_parts_config_dir = os.path.join(self.productdefine_dir,
                                                      'base')


@dataclass
class Outputs:
    def __init__(self, args):
        self.__post_init__(args)

    def __post_init__(self, args):
        self.build_prop = os.path.join(args.preloader_output_dir,
                                            'build.prop')
        self.build_config_json = os.path.join(args.preloader_output_dir,
                                            'build_config.json')
        self.parts_json = os.path.join(args.preloader_output_dir, 'parts.json')
        self.build_gnargs_prop = os.path.join(args.preloader_output_dir,
                                              'build_gnargs.prop')
        self.features_json = os.path.join(args.preloader_output_dir,
                                          'features.json')
        self.subsystem_config_json = os.path.join(args.preloader_output_dir,
                                                  'subsystem_config.json')
        self.platforms_build = os.path.join(args.preloader_output_dir,
                                            'platforms.build')


class Preloader():
    def __init__(self, args):
        # All kinds of directories and subsystem_config_json
        self._configs = Configs(args)

        # Product & Device
        self._product = Product(args.product_name, self._configs)
        self._device = self._product.get_device()

        # All kinds of output files
        self._outputs = Outputs(args)

    def run(self):
        all_parts, build_vars = self._product.parse_config()
        if self._device:
            device_info = self._device.get_device_info()
            if device_info:
                build_vars.update(device_info)

        # save parts to parts_json
        _output_parts_json(all_parts, self._outputs.parts_json)

        # save features to features_json
        all_features = _output_parts_features(all_parts,
                                              self._outputs.features_json)

        # Save gn args to build_gnargs_prop
        _output_gnargs_prop(all_features, self._outputs.build_gnargs_prop)

        # generate toolchain
        os_level = build_vars.get('os_level')
        target_os = build_vars.get('target_os')
        target_cpu = build_vars.get('target_cpu')
        if os_level == 'mini' or os_level == 'small':
            toolchain_label = ""
        else:
            toolchain_label = '//build/toolchain/{0}:{0}_clang_{1}'.format(
                target_os, target_cpu)

        # add toolchain label
        build_vars['product_toolchain_label'] = toolchain_label

        # output platform config
        parts_config_file = os.path.relpath(self._outputs.parts_json,
                                            self._configs.preloader_output_dir)
        _output_platforms_config(target_os, target_cpu, toolchain_label,
                                 parts_config_file,
                                 self._outputs.platforms_build)

        # output build info to file
        _output_build_vars(build_vars, self._outputs.build_prop,
                           self._outputs.build_config_json)

        # output subsystem info to file
        _merge_subsystem_config(self._product, self._device, self._configs,
                                os_level, self._outputs.subsystem_config_json)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-name', required=True)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--product-config-dir', required=True)
    parser.add_argument('--lite-product-config-dir', required=True)
    parser.add_argument('--lite-components-dir', required=True)
    parser.add_argument('--preloader-output-dir', required=True)
    parser.add_argument('--subsystem-config-file', required=True)

    parser.add_argument('--productdefine-dir')
    parser.add_argument('--base-parts-config-dir')
    parser.add_argument('--device-config-dir')

    args = parser.parse_args(argv)
    preloader = Preloader(args)
    preloader.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
