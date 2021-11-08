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

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file, write_file  # noqa: E402, E501
from parse_lite_config import get_lite_parts_list  # noqa: E402


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


def _get_inherit_parts(inherit_config, current_path):
    _parts = {}
    for _config in inherit_config:
        _file = os.path.join(current_path, _config)
        _info = read_json_file(_file)
        if _info is None:
            raise Exception("read file '{}' failed.".format(_file))
        if _info.get('parts'):
            _parts.update(_info.get('parts'))
    return _parts


def _get_device_info(device_name, device_config_path):
    device_config_file = os.path.join(device_config_path,
                                      '{}.json'.format(device_name))
    device_info = read_json_file(device_config_file)
    if device_info and device_info.get('device_name') != device_name:
        raise Exception("device name configuration incorrect in '{}'".format(
            device_config_file))
    return device_info


def _parse_config_v2(config_info, products_config_path, lite_config_path,
                     base_config_dir, device_config_path):
    os_level = config_info.get("type")
    base_parts = _get_base_parts(base_config_dir, os_level)
    all_parts = base_parts

    inherit_config = config_info.get('inherit')
    if inherit_config:
        inherit_parts = _get_inherit_parts(inherit_config,
                                           products_config_path)
        if inherit_parts:
            all_parts.update(inherit_parts)

    current_product_parts = config_info.get("parts")
    if current_product_parts:
        all_parts.update(current_product_parts)

    product_name = config_info.get('product_name')
    product_company = config_info.get('product_company')
    if os_level == 'mini' or os_level == 'small':
        all_parts.update(
            get_lite_parts_list(lite_config_path, product_name,
                                product_company))
    product_device_name = config_info.get('product_device')
    build_configs = {}
    if product_device_name:
        device_info = _get_device_info(product_device_name, device_config_path)
        if device_info:
            build_configs.update(device_info)
    build_configs['os_level'] = os_level
    build_configs['product_name'] = product_name
    build_configs['product_company'] = product_company
    build_configs['device_name'] = product_device_name
    return all_parts, build_configs


def _parse_config_v1(config_info):
    build_configs = {"os_level": 'large'}
    return {}, build_configs


def _parse_config(product_name, products_config_path, lite_config_path,
                  base_parts_config_path, device_config_path):
    curr_config_file = _get_product_config(products_config_path, product_name)
    config_info = read_json_file(curr_config_file)
    config_version = None
    if config_info:
        config_version = config_info.get('version')
    if not config_version:
        config_version = "1.0"
    if config_version == "2.0":
        if config_info and product_name != config_info.get('product_name'):
            raise Exception(
                "product name configuration incorrect in '{}'".format(
                    curr_config_file))
        return _parse_config_v2(config_info, products_config_path,
                                lite_config_path, base_parts_config_path,
                                device_config_path)
    else:
        return _parse_config_v1(config_info)


def _copy_platforms_config(product_name, target_os, target_cpu,
                           parts_info_file, platform_config_output_path,
                           toolchain_label):
    _config_info = {
        'target_os': target_os,
        "target_cpu": target_cpu,
        "toolchain": toolchain_label
    }
    _parts_config_file = os.path.relpath(parts_info_file,
                                         platform_config_output_path)
    _config_info['parts_config'] = _parts_config_file
    platform_config_info = {'version': 2, 'platforms': {'phone': _config_info}}
    output_file = os.path.join(platform_config_output_path, 'platforms.build')
    write_json_file(output_file, platform_config_info)


def _get_merge_subsystem_config(product_config_path, device_config_path,
                                subsystem_config_file, output_dir,
                                product_name):
    product_config_file = os.path.join(product_config_path,
                                       '{}.json'.format(product_name))
    output_file = os.path.join(output_dir, 'subsystem_config.json')
    subsystem_info = read_json_file(subsystem_config_file)

    product_subsystem_info = {}
    product_info = read_json_file(product_config_file)
    product_build_path = 'no_path'
    if product_info:
        product_build_path = product_info.get('product_build_path', 'no_path')
    if product_build_path != 'no_path' and product_build_path != '':
        product_subsystem_info['path'] = product_build_path
        product_subsystem_name = "product_{}".format(product_name)
        product_subsystem_info['name'] = product_subsystem_name
        if subsystem_info:
            subsystem_info[product_subsystem_name] = product_subsystem_info

    product_device_name = None
    device_build_path = 'no_path'
    if product_info:
        product_device_name = product_info.get('product_device')
    if product_device_name:
        device_info = _get_device_info(product_device_name, device_config_path)
        if device_info:
            device_build_path = device_info.get('device_build_path', 'no_path')

    device_subsystem_info = {}
    if device_build_path != 'no_path' and device_build_path != '':
        device_subsystem_info['path'] = device_build_path
        device_subsystem_name = "device_{}".format(product_device_name)
        device_subsystem_info['name'] = device_subsystem_name
        if subsystem_info:
            subsystem_info[device_subsystem_name] = device_subsystem_info
    write_json_file(output_file, subsystem_info)


def _output_parts_features(parts_feature_info_file, all_parts):
    all_features = {}
    part_feature_map = {}
    for _part_name, _features in all_parts.items():
        all_features.update(_features)
        if _features:
            part_feature_map[_part_name.split(':')[1]] = list(_features.keys())
    parts_feature_info = {
        "features": all_features,
        "part_to_feature": part_feature_map
    }
    write_json_file(parts_feature_info_file, parts_feature_info)
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


def _run(args):
    products_config_path = os.path.join(args.source_root_dir,
                                        args.products_config_dir)
    product_config_root_path = os.path.dirname(products_config_path)
    lite_config_path = os.path.join(args.source_root_dir,
                                    args.lite_products_config_dir)
    if args.base_parts_config_dir:
        base_parts_config_path = os.path.join(args.source_root_dir,
                                              args.base_parts_config_dir)
    else:
        base_parts_config_path = os.path.join(product_config_root_path, 'base')
    if args.device_config_dir:
        device_config_path = os.path.join(args.source_root_dir,
                                          args.device_config_dir)
    else:
        device_config_path = os.path.join(product_config_root_path, 'device')

    all_parts, build_configs = _parse_config(args.product_name,
                                             products_config_path,
                                             lite_config_path,
                                             base_parts_config_path,
                                             device_config_path)

    os_level = build_configs.get('os_level')
    if os_level not in ['standard', 'large', 'mini', 'small']:
        raise Exception("product config incorrect.")

    product_info_output_path = os.path.join(args.source_root_dir,
                                            args.preloader_output_root_dir,
                                            args.product_name)

    parts_info_file = os.path.join(product_info_output_path, 'parts.json')
    parts_config_info = {"parts": list(all_parts.keys())}
    write_json_file(parts_info_file, parts_config_info)
    # output features
    parts_feature_info_file = os.path.join(product_info_output_path,
                                           'features.json')
    all_part_features = _output_parts_features(parts_feature_info_file,
                                               all_parts)
    # write build_gnargs.prop
    part_featrues_prop_file = os.path.join(product_info_output_path,
                                           'build_gnargs.prop')
    all_features_list = _part_features_to_list(all_part_features)
    write_file(part_featrues_prop_file, '\n'.join(all_features_list))

    # generate toolchain
    # deps features info and build config info
    target_os = build_configs.get('target_os')
    target_cpu = build_configs.get('target_cpu')
    if os_level == 'mini' or os_level == 'small':
        toolchain_label = ""
    else:
        toolchain_label = '//build/toolchain/{0}:{0}_clang_{1}'.format(
            target_os, target_cpu)

    # add toolchain label
    build_configs['product_toolchain_label'] = toolchain_label

    # output platform config
    _copy_platforms_config(args.product_name, target_os, target_cpu,
                           parts_info_file, product_info_output_path,
                           toolchain_label)

    # output build info to file
    _build_info_list = []
    build_info_file = os.path.join(product_info_output_path, 'build.prop')
    for k, v in build_configs.items():
        _build_info_list.append('{}={}'.format(k, v))
    write_file(build_info_file, '\n'.join(_build_info_list))
    build_info_json_file = os.path.join(product_info_output_path,
                                        'build_config.json')
    write_json_file(build_info_json_file, build_configs)

    # output subsystem info to file
    subsystem_config_file = os.path.join(args.source_root_dir, 'build',
                                         'subsystem_config.json')
    _get_merge_subsystem_config(products_config_path, device_config_path,
                                subsystem_config_file,
                                product_info_output_path, args.product_name)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-name', required=True)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--products-config-dir', required=True)
    parser.add_argument('--lite-products-config-dir', required=True)
    parser.add_argument('--base-parts-config-dir')
    parser.add_argument('--device-config-dir')
    parser.add_argument('--preloader-output-root-dir', required=True)
    args = parser.parse_args(argv)
    _run(args)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
