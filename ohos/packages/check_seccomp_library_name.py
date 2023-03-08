#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
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
#

import sys
import argparse
import json
import os


class ValidateError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


def parse_cfg_file(file_name):
    """
    Load the cfg file in JSON format
    """
    services_name = set()
    with open(file_name) as fp:
        data = json.load(fp)
        if "services" not in data:
            return services_name
        for field in data['services']:
            services_name.add(field['name'])
    return services_name


def collect_cfg_services_name(cfg_dir):
    services_name = set()
    if not os.path.exists(cfg_dir):
        return services_name
    for file in os.listdir(cfg_dir):
        if file.endswith(".cfg"):
            services_name |= parse_cfg_file("{}/{}".format(cfg_dir, file))
    return services_name


def collect_seccomp_services_name(lib_dir):
    services_name = set()
    name_allow_list = ['system', 'app']
    if not os.path.exists(lib_dir):
        return services_name
    for file in os.listdir(lib_dir):
        if not file.startswith('lib') or not file.endswith('_filter.z.so'):
            raise ValidateError('seccomp directory has other shared library except seccomp policy library')

        front_pos = file.find('lib') + 3
        rear_pos = file.find('_filter.z.so')
        name = file[front_pos : rear_pos]
        if not name.startswith('com.') and name not in name_allow_list:
            services_name.add(name)

    return services_name


def check_seccomp_services_name(servces_name, seccomp_services_name):
    for name in seccomp_services_name:
        if name not in servces_name:
            raise ValidateError('service name  {} not in cfg, please check the name used for seccomp'.format(name))
    return


def main():
    parser = argparse.ArgumentParser(
      description='check whehter name is legal used for the seccomp policy shared library')
    parser.add_argument('--vendor-cfg-path', type=str,
                        help=('input vendor cfg path\n'))

    parser.add_argument('--vendor-seccomp-lib-path', type=str,
                        help=('input vendor seccomp cfg path\n'))

    parser.add_argument('--system-cfg-path', type=str,
                        help=('input system cfg path\n'))

    parser.add_argument('--system-seccomp-lib-path', type=str,
                        help='input system seccomp cfg path\n')

    args = parser.parse_args()
    vendor_services_name = collect_cfg_services_name(args.vendor_cfg_path)
    vendor_seccomp_services_name = collect_seccomp_services_name(args.vendor_seccomp_lib_path)
    check_seccomp_services_name(vendor_services_name, vendor_seccomp_services_name)

    system_services_name = collect_cfg_services_name(args.system_cfg_path)
    system_seccomp_services_name = collect_seccomp_services_name(args.system_seccomp_lib_path)
    check_seccomp_services_name(system_services_name, system_seccomp_services_name)


if __name__ == '__main__':
    sys.exit(main())
