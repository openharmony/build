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
import sys
import argparse
import logging

import build_utils as utils


def _get_arch_type(lib_arch_list):
    is64 = False
    is32 = False
    if ('arm64' in lib_arch_list or 'linux_x86_64' in lib_arch_list
            or 'x86_64' in lib_arch_list):
        is64 = True
    if ('arm' in lib_arch_list or 'linux_x86' in lib_arch_list
            or 'x86' in lib_arch_list):
        is32 = True
    result = None
    if is64 and is32:
        result = 'both'
    elif is64:
        result = '64'
    elif is32:
        result = '32'
    return result


def _cc_library_handle(module_name, library_config, support_arch_list,
                       current_product_arch):
    modules = []
    if 'src' not in library_config or len(library_config.get('src')) == 0:
        return modules
    lib_arch_list = []
    for arch in library_config.get('src'):
        if 'arch' not in arch or 'lib' not in arch:
            logging.error(
                'lib configuration error, missing arch or lib attribute.')
            sys.exit(1)
        arch_value = arch.get('arch')
        if arch_value not in support_arch_list:
            continue
        lib_arch_list.append(arch_value)

    if not lib_arch_list:
        return modules

    arch_type = _get_arch_type(lib_arch_list)
    if arch_type == 'both':
        modules.append(module_name)
        if current_product_arch == 'arm64' or current_product_arch == 'x86_64':
            modules.append('{}_32'.format(module_name))
    elif arch_type == '64':
        modules.append(module_name)
    elif arch_type == '32':
        if current_product_arch == "arm" or current_product_arch == "x86":
            modules.append(module_name)
        else:
            modules.append('{}_32'.format(module_name))
    else:
        logging.error('lib arch configuration error.')
        sys.exit(1)
    return modules


def _java_library_handle(module_name, java_libraries, support_java_type_list):
    modules = []
    for java_lib in java_libraries:
        type_value = java_lib.get('type')
        if type_value not in support_java_type_list:
            continue
        if type_value == 'class':
            modules.append(module_name)
        if type_value == 'maple_so':
            modules.append('libmaple{}'.format(module_name))
    return modules


def _module_process(config_libs, current_product_arch, support_arch_list,
                    support_java_type_list):
    _result = {
        'shared_library': [],
        'static_library': [],
        'header_library': [],
        'host': [],
        'java': []
    }
    for config_lib in config_libs:
        module_name = config_lib.get("name")
        if not module_name:
            logging.error('lib configuration error, missing name attribute.')
            sys.exit(1)
        if 'shared_library' in config_lib:
            _modules = _cc_library_handle(module_name,
                                          config_lib.get('shared_library'),
                                          support_arch_list,
                                          current_product_arch)
            _result.get('shared_library').extend(_modules)
        elif 'static_library' in config_lib:
            _modules = _cc_library_handle(module_name,
                                          config_lib.get('static_library'),
                                          support_arch_list,
                                          current_product_arch)
            _result.get('static_library').extend(_modules)
        elif 'header_library' in config_lib:
            _modules = _cc_library_handle(module_name,
                                          config_lib.get('header_library'),
                                          support_arch_list,
                                          current_product_arch)
            _result.get('header_library').extend(_modules)
        elif 'host' in config_lib:
            _result.get('host').append(module_name)
        elif 'java' in config_lib:
            _modules = _java_library_handle(module_name,
                                            config_lib.get('java'),
                                            support_java_type_list)
            _result.get('java').extend(_modules)
    return _result


def get_sdk_dep_modules(dep_libs_config_file, product_build_info):
    config_data = utils.read_json_file(dep_libs_config_file)
    if config_data is None:
        logging.error("read file '{}' failed.".format(dep_libs_config_file))
        sys.exit(1)

    current_product_arch = product_build_info.get('TARGET_ARCH')
    target_arch_type = product_build_info.get('TARGET_ARCH_TYPE')
    config_support_list = config_data.get("support_arch")
    support_arch_list = utils.get_support_arch_list(config_support_list,
                                                    target_arch_type)
    support_java_type_list = ['class']

    config_libs = config_data.get('libs')
    modules_info = _module_process(config_libs, current_product_arch,
                                   support_arch_list, support_java_type_list)
    return modules_info


if __name__ == '__main__':
    sys.exit(0)
