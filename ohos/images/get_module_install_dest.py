#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


import argparse
import os
import sys


def get_source_name(module_type, name, prefix_override, suffix):
    """generate source file name by type"""
    if (module_type == 'lib' or module_type == 'lib64') and not prefix_override:
        if not name.startswith('lib'):
            name = 'lib' + name
    alias = ''
    if suffix:
        name = name + suffix
    if module_type == 'none':
        name = ''
    return name, alias


def gen_install_dests(system_base_dir, source_file_name, install_images, module_install_dir, relative_install_dir, module_type):
    """generate module install dir by user config"""
    dest = ''
    _install_dir = ''
    for image in install_images:
        if image != 'system':
            continue
        if module_install_dir != '':
            _install_dir = os.path.join(system_base_dir, module_install_dir)
        elif relative_install_dir != '':
            _install_dir = os.path.join(
                system_base_dir, module_type, relative_install_dir)
        else:
            _install_dir = os.path.join(system_base_dir, module_type)
    dest = os.path.join(_install_dir, source_file_name)
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--system-base-dir', required=True,
                        help='system base dir')
    parser.add_argument('--install-images', nargs='+', help='install images')
    parser.add_argument('--module-install-dir', required=False,
                        default='', help='module install dir')
    parser.add_argument('--relative-install-dir', required=False,
                        default='', help='relative install dir')
    parser.add_argument('--type', required=True, help='module type')
    parser.add_argument('--install-name', required=True,
                        help='module install name')
    parser.add_argument('--prefix-override', dest='prefix_override',
                        action='store_true', help='prefix override')
    parser.set_defaults(prefix_override=False)
    parser.add_argument('--suffix', required=False, default='', help='suffix')
    parser.add_argument('--allowed-lib-list', help='')
    args = parser.parse_args()

    source_file_name = ''
    source_file_name, alt_source_file_name = get_source_name(
        args.type, args.install_name, args.prefix_override, args.suffix)
    install_dest = ''
    if args.install_images:
        install_dest = gen_install_dests(args.system_base_dir, source_file_name, args.install_images,
                                         args.module_install_dir, args.relative_install_dir, args.type)
    with open(args.allowed_lib_list, 'r') as f:
        lines = f.readlines()
    lines = [line.strip()[1:] for line in lines]
    if install_dest in lines:
        return 0
    else:
        print(f"{install_dest} not in allowed_so_list")


if __name__ == '__main__':
    sys.exit(main())
