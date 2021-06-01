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

import argparse
import logging
import os
import shutil
import sys
import tempfile

import build_utils as utils

_RESOURCE_TYPE_ALLOWLIST = ['file', 'dir', 'ref']


def _get_placeholder_values(product_build_info):
    values = {}
    product_platform = product_build_info.get('TARGET_PRODUCT')
    values['PRODUCT_PLATFORM'] = product_platform
    values['PRODUCT_DEVICE'] = product_build_info.get('PRODUCT_DEVICE')
    _variant_dirs = utils.get_product_arch_variant_dir(product_build_info)
    values['TARGET_ARCH_VARIANT_1ST'] = _variant_dirs.get('1st')
    target_arch_type = product_build_info.get('TARGET_ARCH_TYPE')
    if target_arch_type == '64_32':
        values['TARGET_ARCH_VARIANT_2ND'] = _variant_dirs.get('2nd')
        values['ARM_OBJ_TARGET'] = 'obj_arm'
    else:
        values['TARGET_ARCH_VARIANT_2ND'] = _variant_dirs.get('1st')
        values['ARM_OBJ_TARGET'] = 'obj'
    return values


def _placeholder(input_str, values):
    return input_str.format(**values)


def _src_file_check(resource_type, src_file):
    if not os.path.exists(src_file):
        logging.error(
            "library resource file '{}' doesn't exist.".format(src_file))
        raise Exception('library resource file not exist.')
    # check resource type
    if resource_type == 'file':
        if not os.path.isfile(src_file):
            logging.error("library resource type is not file")
            raise Exception('library resource type error.')
    elif resource_type == 'dir':
        if not os.path.isdir(src_file):
            logging.error("library resource type is not dir")
            raise Exception('library resource type error.')


def _handler(out_dir, lib_resource, values, is_verify):
    resource_type = lib_resource.get('type', 'file')
    src_file = lib_resource.get('src')
    src_file = _placeholder(src_file, values)

    if resource_type not in ['file', 'dir']:
        logging.error("resource type '{}' not support.".format(resource_type))
        raise Exception('resource type not support.')

    if is_verify:
        _src_file_check(resource_type, src_file)

    _dest_dir = out_dir
    if lib_resource.get('dest'):
        _config_dest = lib_resource.get('dest')
        _config_dest = _placeholder(_config_dest, values)
        _dest_dir = os.path.join(out_dir, _config_dest)

    if lib_resource.get('install_name'):
        _dest_dir = os.path.join(_dest_dir, lib_resource.get('install_name'))
    else:
        basename = os.path.basename(src_file)
        if not basename:
            basename = os.path.basename(src_file.rsplit('/', 1)[0])
        _dest_dir = os.path.join(_dest_dir, basename)

    resource_info = {'type': resource_type, 'src': src_file, 'dest': _dest_dir}
    return resource_info


def _ref_handler(root_dir, lib_resource, parent_path):
    libs_config_file = os.path.join(root_dir, parent_path,
                                    lib_resource.get('config'))
    if not os.path.exists(libs_config_file):
        logging.error(
            "library resource sub-config file '{}' doesn't exist.".format(
                libs_config_file))
        raise Exception('sub-config file not exist.')

    res_list = utils.read_json_file(libs_config_file)
    if res_list is None:
        raise Exception('read sub-config error.')
    return res_list


def _get_resource_list(root_dir,
                       out_dir,
                       resource_config_file,
                       libs_type,
                       values,
                       is_verify=True):
    resource_config = utils.read_json_file(resource_config_file)
    if resource_config is None:
        logging.error("read file '{}' failed.".format(resource_config_file))
        sys.exit(1)
    resource_list = []
    for lib_resource in resource_config.get(libs_type):
        resource_type = lib_resource.get('type', 'file')

        if resource_type not in _RESOURCE_TYPE_ALLOWLIST:
            logging.error('resource type configuration error.')
            raise Exception('resource type configuration error.')

        if resource_type == 'ref':
            _parent_path = os.path.dirname(resource_config_file)
            _resource_list = _ref_handler(root_dir, lib_resource, _parent_path)
            for _resource in _resource_list:
                _res_info = _handler(out_dir, _resource, values, is_verify)
                resource_list.append(_res_info)
        else:
            _res_info = _handler(out_dir, lib_resource, values, is_verify)
            resource_list.append(_res_info)
    return resource_list


def _copy_libs_resource(root_dir, resource_list):
    for resource in resource_list:
        src = os.path.join(root_dir, resource.get('src'))
        dest = os.path.join(root_dir, resource.get('dest'))
        dirname = os.path.dirname(dest)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if resource.get('type') == 'dir':
            utils.copy_dir(src, dest)
        else:
            shutil.copy2(src, dest)


def get_target_list(resource_config_file, libs_type, product_build_info):
    """Get target output file by configuration."""
    target_list = []
    root_dir = utils.get_topdir()
    _placeholder_values = _get_placeholder_values(product_build_info)
    with tempfile.TemporaryDirectory() as tmpdir:
        resource_list = _get_resource_list(root_dir,
                                           tmpdir,
                                           resource_config_file,
                                           libs_type,
                                           _placeholder_values,
                                           is_verify=False)
        for resource in resource_list:
            if resource.get('type') != 'file':
                continue
            src = resource.get('src')
            if not src.startswith('out'):
                continue
            target_list.append(src)
        return target_list


def main(argv):
    """Copy resource files by configuration."""
    parser = argparse.ArgumentParser()
    parser.add_argument('libs_type',
                        choices=[
                            'base_libs', 'prebuilt_resources',
                            'platforms_libs', 'maple_libs'
                        ])
    parser.add_argument('--product-build-prop-file', required=True)
    parser.add_argument('--libs-config-file',
                        required=True,
                        help='config file')
    parser.add_argument('--out-dir', required=True, default='out/a_sdk')
    args = parser.parse_args(argv)

    product_build_info = utils.parse_product_build_info(
        args.product_build_prop_file)
    if not product_build_info:
        logging.error("read file '{}' failed or config data incorrect.".format(
            args.product_build_prop_file))
        return 1

    config_data = utils.read_json_file(args.libs_config_file)
    if config_data is None:
        logging.error("read file '{}' failed or config data incorrect.".format(
            args.libs_config_file))
        return 1

    _placeholder_values = _get_placeholder_values(product_build_info)
    root_dir = utils.get_topdir()

    if args.libs_type == 'base_libs':
        target_arch_type = product_build_info.get('TARGET_ARCH_TYPE')
        libs_type = 'base_libs_{}'.format(target_arch_type)
    else:
        libs_type = args.libs_type
    resource_list = _get_resource_list(root_dir, args.out_dir,
                                       args.libs_config_file, libs_type,
                                       _placeholder_values)
    copy_resource_file = os.path.join(args.out_dir, 'copy_res_list.json')
    utils.write_json_file(copy_resource_file, resource_list)

    _copy_libs_resource(root_dir, resource_list)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
