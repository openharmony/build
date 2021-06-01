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
import libs_resource_copy

import libs_sdk_dep_modules as dep_modules

DEP_SHARED_LIBRARY_ALLOWLIST = ['libandroidicu']


def _get_dep_modules(dep_libs_config_file, product_build_info):
    modules_info = dep_modules.get_sdk_dep_modules(dep_libs_config_file,
                                                   product_build_info)
    dep_list = []
    dep_list.extend(modules_info.get('static_library'))
    dep_list.extend(modules_info.get('header_library'))
    dep_list.extend(modules_info.get('host'))
    if DEP_SHARED_LIBRARY_ALLOWLIST:
        product_out = os.path.join('out/target/product',
                                   product_build_info.get('PRODUCT_DEVICE'))
        shared_libs = modules_info.get('shared_library')
        for _modules_name in DEP_SHARED_LIBRARY_ALLOWLIST:
            module_file = os.path.join(
                product_out, 'obj', 'SHARED_LIBRARIES',
                '{}_intermediates'.format(_modules_name),
                '{}.so'.format(_modules_name))
            dep_list.append(module_file)

            if '{}_32'.format(_modules_name) in shared_libs:
                module_file_32 = os.path.join(
                    product_out, 'obj_arm', 'SHARED_LIBRARIES',
                    '{}_intermediates'.format(_modules_name),
                    '{}.so'.format(_modules_name))
                dep_list.append(module_file_32)
    return dep_list


def _get_base_libs(base_libs_config_file, product_build_info):
    target_arch_type = product_build_info.get('TARGET_ARCH_TYPE')
    libs_type = 'base_libs_{}'.format(target_arch_type)
    _list = libs_resource_copy.get_target_list(base_libs_config_file,
                                               libs_type, product_build_info)
    return _list


def main(argv):
    """Get module real target by asdk configuration."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-build-prop-file', required=True)
    parser.add_argument('--base-libs-config-file', required=True)
    parser.add_argument('--dep-libs-config-file', required=True)
    parser.add_argument('--output-base-libs', required=True)
    parser.add_argument('--output-dep-libs', required=True)
    args = parser.parse_args(argv)
    product_build_info = utils.parse_product_build_info(
        args.product_build_prop_file)

    base_modules_list = _get_base_libs(args.base_libs_config_file,
                                       product_build_info)
    utils.write_file(args.output_base_libs, ' '.join(base_modules_list))

    if args.dep_libs_config_file:
        dep_modules_list = _get_dep_modules(args.dep_libs_config_file,
                                            product_build_info)
        utils.write_file(args.output_dep_libs, ' '.join(dep_modules_list))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
