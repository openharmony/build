#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

from util.file_utils import read_json_file
from util.build_utils import touch, check_instance


def read_hap_file(file_path: str):
    hvigor_compile_hap_allow_info = read_json_file(file_path)
    if hvigor_compile_hap_allow_info:
        return hvigor_compile_hap_allow_info
    else:
        raise Exception(f'the file: {file_path} is not exist')


def check_sdk_version(args, hvigor_compile_hap_allow_info):
    if not args.sdk_home or hvigor_compile_hap_allow_info is None:
        return 0

    sdk_allow_version_list = hvigor_compile_hap_allow_info.get("sdk_version")
    check_instance(sdk_allow_version_list, "sdk_version", dict)

    message = "The hap path name: '{}' use the sdk version: '{}', but it is not exist in whitelist, please check target: '{}'".format(args.target_path, args.sdk_home, args.hvigor_compile_hap_allow_file)

    if args.sdk_home not in sdk_allow_version_list:
        return 0

    if args.target_path not in sdk_allow_version_list.get(args.sdk_home):
        raise Exception(message)

    return 0


def check_hvigor_version(args, hvigor_compile_hap_allow_info):
    if not args.hvigor_home or hvigor_compile_hap_allow_info is None:
        return 0
    
    hvigor_allow_version_list = hvigor_compile_hap_allow_info.get("hvigor_version")
    check_instance(hvigor_allow_version_list, "hvigor_version", dict)

    message = "The hap path name: '{}' use the hvigor version: '{}', but it is not exist in whitelist, please check target: '{}'".format(args.target_path, args.hvigor_home, args.hvigor_compile_hap_allow_file)
    
    if args.hvigor_home not in hvigor_allow_version_list:
        return 0
    
    if args.target_path not in hvigor_allow_version_list.get(args.hvigor_home):
        raise Exception(message)
    
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target-path', required=True, default='')
    parser.add_argument('--output', required=True)
    parser.add_argument('--hvigor-compile-hap-allow-file', required=True)
    parser.add_argument('--sdk-home', help='sdk home')
    parser.add_argument('--hvigor-home', help='hvigor home')
    args = parser.parse_args()

    # read hvigor compile hap allow list file
    hvigor_compile_hap_allow_info = read_hap_file(args.hvigor_compile_hap_allow_file)

    # check sdk version
    check_sdk_version(args, hvigor_compile_hap_allow_info)

    # check hvigor version
    check_hvigor_version(args, hvigor_compile_hap_allow_info)

    touch(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
