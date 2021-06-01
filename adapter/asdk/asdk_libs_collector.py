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

import sys
import os
import argparse
import shutil

import build_utils as utils
import build_libs
import create_build_gn
import libs_resource_copy


def _get_asdk_modules(product_build_prop_file, dep_libs_config_file,
                      asdk_out_dir, enable_java):
    _args = ['gen-modules']
    _args.extend(['--product-build-prop-file', product_build_prop_file])
    _args.extend(['--libs-config-file', dep_libs_config_file])
    _args.extend(['--out-dir', asdk_out_dir])
    if enable_java:
        _args.append('--enable-java')
    return_code = build_libs.main(_args)
    if return_code != 0:
        raise Exception("build: run build_libs.py gen-modules failed.")


def _generate_build_gn(asdk_out_dir):
    _args = ['--libs-config-file']
    _args.append(os.path.join(asdk_out_dir, 'module_info.json'))
    _args.extend(['--out-dir', asdk_out_dir])
    return_code = create_build_gn.main(_args)
    if return_code != 0:
        raise Exception("build: run create_build_gn.py failed.")


def _copy_asdk_libs(asdk_out_dir, asdk_libs_target_dir, enable_java):
    base_libs_target_dir = os.path.join(asdk_libs_target_dir, 'ndk')
    if os.path.exists(base_libs_target_dir):
        shutil.rmtree(base_libs_target_dir)
    shutil.copytree(os.path.join(asdk_out_dir, 'base_libs'),
                    base_libs_target_dir)

    sdk_libs_target_dir = os.path.join(asdk_libs_target_dir, 'sdk')
    if os.path.exists(sdk_libs_target_dir):
        shutil.rmtree(sdk_libs_target_dir)
    os.makedirs(sdk_libs_target_dir, exist_ok=True)
    shutil.copy2(os.path.join(asdk_out_dir, 'module_info.json'),
                 sdk_libs_target_dir)
    shutil.copytree(os.path.join(asdk_out_dir, 'shared_library'),
                    os.path.join(sdk_libs_target_dir, 'shared_library'))
    if os.path.exists(os.path.join(asdk_out_dir, 'static_library')):
        shutil.copytree(os.path.join(asdk_out_dir, 'static_library'),
                        os.path.join(sdk_libs_target_dir, 'static_library'))
    if os.path.exists(os.path.join(asdk_out_dir, 'host')):
        shutil.copytree(os.path.join(asdk_out_dir, 'host'),
                        os.path.join(sdk_libs_target_dir, 'host'))
    if enable_java and os.path.exists(os.path.join(asdk_out_dir, 'java')):
        shutil.copytree(os.path.join(asdk_out_dir, 'java'),
                        os.path.join(sdk_libs_target_dir, 'java'))
    if enable_java and os.path.exists(os.path.join(asdk_out_dir, 'maple2.0')):
        shutil.copytree(os.path.join(asdk_out_dir, 'maple2.0'),
                        os.path.join(sdk_libs_target_dir, 'maple2.0'))
    if enable_java and os.path.exists(os.path.join(asdk_out_dir, 'platforms')):
        shutil.copytree(os.path.join(asdk_out_dir, 'platforms'),
                        os.path.join(sdk_libs_target_dir, 'platforms'))


def _get_base_libs(product_build_prop_file, base_libs_config_file,
                   asdk_out_dir):
    _args = ['base_libs']
    _args.append('--product-build-prop-file')
    _args.append(product_build_prop_file)
    _args.append('--libs-config-file')
    _args.append(base_libs_config_file)
    _args.append('--out-dir')
    _args.append(os.path.join(asdk_out_dir, 'base_libs'))
    return_code = libs_resource_copy.main(_args)
    if return_code != 0:
        raise Exception(
            "build: run libs_resource_copy.py copy base libs failed.")


def _get_maple_libs(product_build_prop_file, maple_libs_config_file,
                    asdk_out_dir):
    _args = ['maple_libs']
    _args.extend(['--product-build-prop-file', product_build_prop_file])
    _args.extend(['--libs-config-file', maple_libs_config_file])
    _args.extend(['--out-dir', os.path.join(asdk_out_dir, 'maple2.0')])
    return_code = libs_resource_copy.main(_args)
    if return_code != 0:
        raise Exception(
            "build: run libs_resource_copy.py copy base libs failed.")


def _get_platforms_libs(product_build_prop_file, platforms_libs_config_file,
                        asdk_out_dir):
    _args = ['platforms_libs']
    _args.extend(['--product-build-prop-file', product_build_prop_file])
    _args.extend(['--libs-config-file', platforms_libs_config_file])
    _args.extend(['--out-dir', os.path.join(asdk_out_dir, 'platforms')])
    return_code = libs_resource_copy.main(_args)
    if return_code != 0:
        raise Exception(
            "build: run libs_resource_copy.py copy base libs failed.")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-build-prop-file', required=True)
    parser.add_argument('--base-libs-config-file', required=True)
    parser.add_argument('--dep-libs-config-file', required=True)
    parser.add_argument('--maple-libs-config-file')
    parser.add_argument('--platforms-libs-config-file')
    parser.add_argument('--asdk-dir', required=True)
    parser.add_argument('--asdk-libs-target-dir', required=True)
    parser.add_argument('--enable-java',
                        dest='enable_java',
                        action='store_true')
    parser.set_defaults(enable_java=False)
    args = parser.parse_args(argv)

    _get_base_libs(args.product_build_prop_file, args.base_libs_config_file,
                   args.asdk_dir)

    _get_asdk_modules(args.product_build_prop_file, args.dep_libs_config_file,
                      args.asdk_dir, args.enable_java)
    _generate_build_gn(args.asdk_dir)
    if args.enable_java:
        if args.maple_libs_config_file:
            _get_maple_libs(args.product_build_prop_file,
                            args.maple_libs_config_file, args.asdk_dir)
        if args.platforms_libs_config_file:
            _get_platforms_libs(args.product_build_prop_file,
                                args.platforms_libs_config_file, args.asdk_dir)
    _copy_asdk_libs(args.asdk_dir, args.asdk_libs_target_dir, args.enable_java)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
