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

import argparse
from dataclasses import dataclass
import glob
import os
import sys
import re

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from loader.preloader.parse_lite_subsystems_config import parse_lite_subsystem_config  # noqa: E402, E501
from loader.preloader.parse_vendor_product_config import get_vendor_parts_list, get_product_config  # noqa: E402, E501
from scripts.util.file_utils import read_json_file, write_file, write_json_file  # noqa: E402, E501


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


def _get_inherit_parts(inherit, source_root_dir):
    inherit_parts = {}
    for _config in inherit:
        _file = os.path.join(source_root_dir, _config)
        _info = read_json_file(_file)
        if _info is None:
            raise Exception("read file '{}' failed.".format(_file))
        parts = _info.get('parts')
        if parts:
            inherit_parts.update(parts)
    return inherit_parts


def _get_product_config(built_in_dir, vendor_dir, product_name):
    config_file = os.path.join(built_in_dir, '{}.json'.format(product_name))
    if not os.path.exists(config_file):
        config_files = glob.glob('{}/**/config.json'.format(vendor_dir),
                                 recursive=True)
        for config_file in config_files:
            config = read_json_file(config_file)
            if config and config.get('product_name') == product_name:
                return config, config_file
        raise Exception(
            "product configuration files for '{}' doesn't exist.".format(
                product_name))
    else:
        config = read_json_file(config_file)
        if config is None:
            config = {}
        return config, config_file


def _get_device_info(device_name, config_dir):
    device_config_file = os.path.join(config_dir,
                                      '{}.json'.format(device_name))
    device_info = read_json_file(device_config_file)
    if device_info and device_info.get('device_name') != device_name:
        raise Exception("device name configuration incorrect in '{}'".format(
            device_config_file))
    if device_info is None:
        device_info = {}
    return device_info


def _output_platforms_config(target_os, target_cpu, toolchain_label,
                             parts_config_file, output_file):
    config = {
        'target_os': target_os,
        "target_cpu": target_cpu,
        "toolchain": toolchain_label,
        "parts_config": parts_config_file
    }

    platform_config = {'version': 2, 'platforms': {'phone': config}}
    write_json_file(output_file, platform_config)


def _output_gnargs_prop(all_features, output_file):
    features_list = _part_features_to_list(all_features)
    write_file(output_file, '\n'.join(features_list))


def _get_org_subsytem_info(subsystem_config_file, os_level, config_dirs):
    subsystem_info = {}
    if os_level == "standard":
        subsystem_info = read_json_file(subsystem_config_file)
        if subsystem_info is None:
            subsystem_info = {}
    elif os_level == "mini" or os_level == "small":
        ohos_build_output_dir = os.path.join(config_dirs.preloader_output_dir,
                                             '{}_system'.format(os_level))
        subsystem_info = parse_lite_subsystem_config(
            config_dirs.lite_components_dir, ohos_build_output_dir,
            config_dirs.source_root_dir)
    return subsystem_info


def _merge_subsystem_config(product, device, config_dirs, os_level,
                            output_file):
    subsystem_info = _get_org_subsytem_info(config_dirs.subsystem_config_json,
                                            os_level, config_dirs)
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
    def __init__(self, product_name, config_dirs):
        self._name = product_name
        self._dirs = config_dirs
        self._device = None
        self._config = {}
        self._build_vars = {}
        self._parts = {}
        self._parsed = False
        self._config_file = ''

    def parse_config(self):
        self._do_parse()
        return self._parts, self._build_vars

    def get_device(self):
        self._do_parse()
        return self._device

    def get_product_specific_subsystem(self):
        info = {}
        self._do_parse()
        subsystem_name = 'product_{}'.format(self._name)
        if self._get_product_build_path():
            info[subsystem_name] = {
                'name': subsystem_name,
                'path': self._get_product_build_path()
            }
        return info

    def _get_product_build_path(self):
        return self._config.get('product_build_path')

    def _do_parse(self):
        if self._parsed is False:
            self._config, self._config_file = _get_product_config(
                self._dirs.built_in_product_dir, self._dirs.vendor_dir,
                self._name)

            version = self._config.get('version')
            if version is None:
                version = "1.0"

            if version == "1.0":
                self._parse_config_v1()
            else:
                self._parse_config_v2p(self._config, version)
            self._parsed = True

    def _get_product_specific_parts(self):
        part_name = 'product_{}'.format(self._name)
        subsystem_name = part_name
        info = {}
        info['{}:{}'.format(subsystem_name, part_name)] = {}
        return info

    def _parse_config_v2(self, config):
        all_parts = {}

        os_level = config.get("type")
        device_name = config.get('product_device')
        if os_level == 'mini' or os_level == 'small':
            lite_config = get_product_config(self._dirs.vendor_dir, self._name,
                                             config['product_company'])
            all_parts.update(get_vendor_parts_list(lite_config))
            all_parts.update(self._get_product_specific_parts())
            if self._device:
                all_parts.update(self._device.get_device_specific_parts())
        else:
            current_product_parts = config.get("parts")
            if current_product_parts:
                all_parts.update(current_product_parts)

        build_vars = {}
        build_vars['os_level'] = os_level
        build_vars['product_name'] = config.get('product_name')
        if device_name:
            build_vars['device_name'] = device_name
        else:
            build_vars['device_name'] = ''
        build_vars['product_company'] = config.get('product_company')

        self._build_vars = build_vars
        self._parts.update(all_parts)

        device_name = config.get('product_device')
        if device_name:
            self._device = Device(device_name, self._dirs)

    # Generate build_info needed for V3 configuration
    def _make_device_info(self, config):
        # NOTE:
        # Product_name, device_company are necessary for
        # config.json, DON NOT use .get to replace []
        device_info = {
            'device_name': config['product_name'],
            'device_company': config['device_company']
        }
        if config.get('target_os'):
            device_info['target_os'] = config.get('target_os')
        else:
            device_info['target_os'] = 'ohos'

        if config.get('target_cpu'):
            device_info['target_cpu'] = config['target_cpu']
        else:
            # Target cpu is used to set default toolchain for standard system.
            device_info['target_cpu'] = 'unknown'
        if config.get('kernel_version'):
            device_info['kernel_version'] = config.get('kernel_version')
        if config.get('device_build_path'):
            device_info['device_build_path'] = config.get('device_build_path')
        else:
            device_build_path = os.path.join(self._dirs.device_dir,
                                             config['device_company'],
                                             config['board'])
            if not os.path.exists(device_build_path):
                device_build_path = os.path.join(self._dirs.device_dir,
                                                 'board',
                                                 config['device_company'],
                                                 config['board'])
            device_info['device_build_path'] = device_build_path

        return device_info

    def _parse_config_v3(self, config):
        all_parts = {}
        all_parts.update(get_vendor_parts_list(config))
        all_parts.update(self._get_product_specific_parts())

        device_name = config.get('board')
        if device_name:
            device_info = self._make_device_info(config)
            self._device = Device(device_name, self._dirs, device_info)
            all_parts.update(self._device.get_device_specific_parts())

        build_vars = {}
        build_vars['os_level'] = config.get('type')
        build_vars['product_name'] = config.get('product_name')
        build_vars['device_name'] = config.get('board')
        if config.get('product_company'):
            build_vars['product_company'] = config.get('product_company')
        elif not self._is_built_in_product(self._config_file):
            relpath = os.path.relpath(self._config_file, self._dirs.vendor_dir)
            build_vars['product_company'] = relpath.split('/')[0]
        else:
            build_vars['product_company'] = config.get('device_company')

        self._build_vars = build_vars
        self._parts.update(all_parts)

        if not self._is_built_in_product(self._config_file) and not hasattr(
                config, 'product_build_path'):
            config['product_build_path'] = os.path.relpath(
                os.path.dirname(self._config_file), self._dirs.source_root_dir)

    def _is_built_in_product(self, config_file):
        if os.path.dirname(config_file) == self._dirs.built_in_product_dir:
            return True
        else:
            return False

    def _sanitize(self, config):
        if config and self._name != config.get('product_name'):
            raise Exception(
                "product name configuration incorrect for '{}'".format(
                    self._name))
        os_level = config.get("type")
        if os_level not in ['standard', 'large', 'mini', 'small']:
            raise Exception("product config incorrect.")

    # parse v2 and plus
    def _parse_config_v2p(self, config, version):
        self._sanitize(config)

        # 1. inherit parts infomation from base config
        os_level = config.get("type")
        self._parts = _get_base_parts(self._dirs.built_in_base_dir, os_level)
        # 2. inherit parts information from inherit config
        inherit = config.get('inherit')
        if inherit:
            self._parts.update(
                _get_inherit_parts(inherit, self._dirs.source_root_dir))

        # 3. get parts information from product config
        if version == '2.0':
            self._parse_config_v2(config)
        else:
            self._parse_config_v3(config)

    def _parse_config_v1(self):
        self._parts = {}
        self._build_vars = {"os_level": 'large'}


class Device():
    def __init__(self, device_name, config_dirs, device_info=None):
        self._name = device_name
        self._dirs = config_dirs
        if device_info is None:
            self._device_info = _get_device_info(
                self._name, self._dirs.built_in_device_dir)
        else:
            self._device_info = device_info

    def get_device_info(self):
        return self._device_info

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
        if self._get_device_build_path():
            info[subsystem_name] = {
                'name': subsystem_name,
                'path': self._get_device_build_path()
            }
        return info

    def _get_device_build_path(self):
        if self._device_info:
            return self._device_info.get('device_build_path')
        else:
            return None


@dataclass
class ConfigDirs:
    def __init__(self, args):
        self.__post_init__(args)

    def __post_init__(self, args):
        self.source_root_dir = args.source_root_dir
        # The following 4 diretories are used for built-in-products only.
        # Hard-coded it in case someone tries to change it.
        self.built_in_product_dir = os.path.join(
            args.source_root_dir, 'productdefine/common/products')
        # Same as built_in_product_dir
        self.productdefine_dir = os.path.join(args.source_root_dir,
                                              'productdefine/common')
        self.built_in_device_dir = os.path.join(self.productdefine_dir,
                                                'device')
        self.built_in_base_dir = os.path.join(self.productdefine_dir, 'base')

        # Configs of vendor specified products are stored in
        # ${vendor_dir} directory.
        self.vendor_dir = args.vendor_dir
        # Configs of device specified products are stored in
        # ${device_dir} directory.
        self.device_dir = args.device_dir

        self.lite_components_dir = args.lite_components_dir
        self.subsystem_config_json = args.subsystem_config_file

        self.preloader_output_dir = args.preloader_output_dir


@dataclass
class Outputs:
    def __init__(self, args):
        self.__post_init__(args)

    def __post_init__(self, args):
        self.build_prop = os.path.join(args.preloader_output_dir, 'build.prop')
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
        self._dirs = ConfigDirs(args)

        # Product & Device
        self._product = Product(args.product_name, self._dirs)
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
                                            self._dirs.preloader_output_dir)
        _output_platforms_config(target_os, target_cpu, toolchain_label,
                                 parts_config_file,
                                 self._outputs.platforms_build)

        # output build info to file
        _output_build_vars(build_vars, self._outputs.build_prop,
                           self._outputs.build_config_json)

        # output subsystem info to file
        _merge_subsystem_config(self._product, self._device, self._dirs,
                                os_level, self._outputs.subsystem_config_json)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-name', required=True)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--vendor-dir', required=True)
    parser.add_argument('--lite-components-dir', required=True)
    parser.add_argument('--preloader-output-dir', required=True)
    parser.add_argument('--device-dir', required=True)

    parser.add_argument('--subsystem-config-file', required=True)

    args = parser.parse_args(argv)
    preloader = Preloader(args)
    preloader.run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
