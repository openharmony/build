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

import sys
import argparse
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.util.file_utils import read_json_file, write_json_file  # noqa: E402 E501


# read subsystem module, generate subsystem install list and deps list.
def gen_output_file(part_name, origin_part_name, all_modules_file,
                    sdk_modules_info_file, install_modules_file,
                    dep_modules_file, output_host_file,
                    current_toolchain, host_toolchain):
    # read subsystem module info
    all_module_info = read_json_file(all_modules_file)
    if all_module_info is None:
        raise Exception(
            "read part '{}' modules info failed.".format(part_name))

    # merge sdk install modules, may be repeat
    if os.path.exists(sdk_modules_info_file):
        sdk_modules_info = read_json_file(sdk_modules_info_file)
        if sdk_modules_info is not None:
            all_module_info.extend(sdk_modules_info)

    # thirdparty subsystem part module list
    thirdparty_module_list = []

    # driver/interface part moudle list
    hdi_module_list = []

    # driver/interface and thirdparty subsystem part module list
    external_module_list = []

    # Generate a list of modules by part
    modules_info_dict = {}
    modules_def = {}  # remove duplicates
    for info in all_module_info:
        module_def = info.get('module_def')
        if module_def in modules_def:
            continue

        modules_def[module_def] = ''
        thirdparty = info.get('subsystem_name')
        if thirdparty == 'thirdparty':
            thirdparty_module_list.append(info)
            external_module_list.append(info)
        if str(module_def).startswith("//drivers/interface"):
            hdi_module_list.append(info)
            external_module_list.append(info)
        _module_part_name = info.get('part_name')
        if _module_part_name not in modules_info_dict:
            modules_info_dict[_module_part_name] = []
        modules_info_dict[_module_part_name] += [info]

    # Current part module list
    part_module_list = []
    if origin_part_name in modules_info_dict:
        part_module_list = modules_info_dict.pop(origin_part_name)

    # Current part dependent module list
    part_install_modules = []
    part_no_install_modules = []
    part_host_modules = []
    for install_module in part_module_list:
        toolchain = install_module.get('toolchain')
        if toolchain == '' or toolchain == current_toolchain:
            part_install_modules.append(install_module)
        else:
            if toolchain == host_toolchain:
                part_host_modules.append(install_module)
            part_no_install_modules.append(install_module)

    for install_module in external_module_list:
        toolchain = install_module.get('toolchain')
        if toolchain == host_toolchain:
            part_host_modules.append(install_module)

    # Depended thirdparty modules and driver/interface modules
    # are installed by default
    # rather than configured in product config.
    part_install_modules.extend(thirdparty_module_list)
    part_install_modules.extend(hdi_module_list)
    # write install modules file
    write_json_file(install_modules_file, part_install_modules)

    # add no install modules to dict, example: host target
    modules_info_dict[part_name] = part_no_install_modules
    # write dep modules file
    write_json_file(dep_modules_file, modules_info_dict)
    write_json_file(output_host_file, part_host_modules)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--part-name', required=True)
    parser.add_argument('--origin-part-name', required=True)
    parser.add_argument('--input-file', help='', required=True)
    parser.add_argument('--sdk-modules-info-file', help='', required=True)
    parser.add_argument('--output-install-file', help='', required=True)
    parser.add_argument('--output-deps-file', help='', required=True)
    parser.add_argument('--output-host-file', help='', required=True)
    parser.add_argument('--current-toolchain', help='', required=True)
    parser.add_argument('--host-toolchain', help='', required=True)
    parser.add_argument('--depfile', required=False)
    args = parser.parse_args()
    gen_output_file(args.part_name, args.origin_part_name, args.input_file,
                    args.sdk_modules_info_file, args.output_install_file,
                    args.output_deps_file, args.output_host_file,
                    args.current_toolchain, args.host_toolchain)
    return 0


if __name__ == '__main__':
    sys.exit(main())
