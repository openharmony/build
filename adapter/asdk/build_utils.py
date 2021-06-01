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

import os
import json
import shutil
import logging
import sys


def get_topdir():
    """Get src root dir."""
    topfile = 'build/make/core/envsetup.mk'
    topdir = os.getcwd()
    while not os.path.exists(os.path.join(topdir, topfile)):
        topdir = os.path.dirname(topdir)
        if topdir == '/':
            print('Cannot find source root dir')
            return None
    return topdir


def parse_product_build_info(product_build_info_file):
    build_info = read_prop_file(product_build_info_file)
    _module_target_arch_type(build_info)
    return build_info


def _module_target_arch_type(product_build_info):
    target_arch = product_build_info.get('TARGET_ARCH')
    target_2nd_arch = product_build_info.get('TARGET_2ND_ARCH')
    _target_arch_type = '64_32'
    if not target_2nd_arch:
        _target_arch_type = '64' if target_arch == 'arm64' else '32'
    product_build_info['TARGET_ARCH_TYPE'] = _target_arch_type


def get_support_arch_list(config_support_list,
                          target_arch_type,
                          first_cpu=True):
    if config_support_list is None or len(config_support_list) == 0:
        logging.error("config error, support arch is empty.")
        sys.exit(1)
    _current_arch_list = []
    if target_arch_type == '64_32' and not first_cpu:
        _current_arch_list.extend(['arm64', 'arm'])
    elif target_arch_type == '32':
        _current_arch_list.append('arm')
    else:
        _current_arch_list.append('arm64')
    support_arch_list = list(
        set(config_support_list).intersection(set(_current_arch_list)))
    if not support_arch_list:
        logging.error('lib configuration error, arch type not support.')
        sys.exit(1)
    return support_arch_list


def get_product_arch_variant_dir(product_info):
    _target_arch = product_info.get('TARGET_ARCH')
    _target_arch_variant = product_info.get('TARGET_ARCH_VARIANT')
    _target_cpu_variant = product_info.get('TARGET_CPU_VARIANT')
    if _target_cpu_variant == 'generic' or _target_cpu_variant == '':
        _arch_path_var = '{}_{}'.format(_target_arch, _target_arch_variant)
    else:
        _arch_path_var = '{}_{}_{}'.format(_target_arch, _target_arch_variant,
                                           _target_cpu_variant)
    product_arch_variant_dir_1st = 'android_{}_core'.format(_arch_path_var)

    _target_2nd_arch = product_info.get('TARGET_2ND_ARCH')
    _target_2nd_arch_variant = product_info.get('TARGET_2ND_ARCH_VARIANT')
    _target_2nd_cpu_variant = product_info.get('TARGET_2ND_CPU_VARIANT')
    if _target_2nd_cpu_variant == 'generic' or _target_2nd_cpu_variant == '':
        _arch_path_var2 = '{}_{}'.format(_target_2nd_arch,
                                         _target_2nd_arch_variant)
    else:
        _arch_path_var2 = '{}_{}_{}'.format(_target_2nd_arch,
                                            _target_2nd_arch_variant,
                                            _target_2nd_cpu_variant)
    product_arch_variant_dir_2nd = 'android_{}_core'.format(_arch_path_var2)
    result = {
        "1st": product_arch_variant_dir_1st,
        "2nd": product_arch_variant_dir_2nd
    }
    return result


def read_json_file(input_file):
    """Read json file data."""
    if not os.path.exists(input_file):
        print('file [{}] no exist.'.format(input_file))
        return None
    data = None
    with open(input_file, 'r') as input_f:
        data = json.load(input_f)
    return data


def write_json_file(output_file, content, sort_keys=False):
    """Write json file data."""
    file_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)

    with open(output_file, 'w') as output_f:
        json.dump(content, output_f, sort_keys=sort_keys)


def write_file(output_file, content, mode='w'):
    """Write file data."""
    file_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(file_dir):
        os.makedirs(file_dir, exist_ok=True)

    with open(output_file, mode) as output_f:
        output_f.write(content)
        output_f.flush()


def read_file(input_file):
    """Read file by line."""
    if not os.path.exists(input_file):
        print("file '{}' doesn't exist.".format(input_file))
        return None

    data = []
    file_obj = None
    try:
        with open(input_file, 'r') as file_obj:
            for line in file_obj.readlines():
                data.append(line.rstrip('\n'))
    except OSError:
        raise Exception("read file '{}' failed".format(input_file))
    return data


def read_prop_file(input_file):
    """Read file by line."""
    if not os.path.exists(input_file):
        print("file '{}' doesn't exist.".format(input_file))
        return None
    data = {}
    file_obj = None
    try:
        with open(input_file, 'r') as file_obj:
            for line in file_obj.readlines():
                _line = line.rstrip('\n')
                if _line.startswith(('#', '=')):
                    continue
                info = _line.split('=', 1)
                data[info[0]] = info[1]
    except OSError:
        raise Exception("read file '{}' failed".format(input_file))
    return data


def _filter_file(file, filter_dict):
    return False


def copy_dir(src_dir, dest_dir, filter_dict=None):
    """Copy dir to dest path."""
    for file_name in os.listdir(src_dir):
        if file_name == '.' or file_name == '..':
            continue
        _file = os.path.join(src_dir, file_name)
        if os.path.isfile(_file) and not _filter_file(_file, filter_dict):
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy2(_file, dest_dir)
        elif os.path.isdir(_file):
            copy_dir(_file, os.path.join(dest_dir, file_name))
        else:
            continue
