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

import json
import os
import sys
import zipfile
import argparse
import time

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file # noqa: E402

sdk_package_list = []
sdk_package_set = set()
sdk_package_location = ""
product_name = ""
sdk_version = ""


def parse_sdk_check_list(sdk_check_list):
    sdk_check_files = []
    sdk_check_directories = []
    sdk_delivery_list = read_json_file(sdk_check_list)

    if sdk_delivery_list is None:
        raise Exception("read file '{}' failed.".format(sdk_check_list))

    if sys.platform == 'linux':
        sdk_check_files = sdk_delivery_list['linux']['checkFiles']
        sdk_check_directories = sdk_delivery_list['linux']['checkDirectories']
        win_sdk_check_files = sdk_delivery_list['windows']['checkFiles']
        win_sdk_check_directories = sdk_delivery_list['windows']['checkDirectories']  
        sdk_check_files.extend(win_sdk_check_files)
        sdk_check_directories.extend(win_sdk_check_directories)
    else:  
        sdk_check_files = sdk_delivery_list['darwin']['checkFiles']
        sdk_check_directories = sdk_delivery_list['darwin']['checkDirectories']

    return sdk_check_files, sdk_check_directories


def add_files_to_sdk_package(sdk_package_directory, compressed_file):
    archive_file = os.path.join(sdk_package_directory, compressed_file)
    is_zipfile = zipfile.is_zipfile(archive_file)
    if is_zipfile: 
        sdk_package_path = sdk_package_directory[sdk_package_directory.find(product_name) + len(product_name) + 1:]
        zip_file = zipfile.ZipFile(archive_file, 'r')
        global sdk_package_list
        zip_file_path = []
        zip_file_namelist = zip_file.namelist()
        for zip_file in zip_file_namelist:
            zip_file_path.append(os.path.join(sdk_package_path, zip_file))
        sdk_package_list.extend(zip_file_path)
    else:
        raise Exception("Error: {} is not zip".format(archive_file))


def get_sdk_package_directories(): 
    if sys.platform == 'linux':
        os_types = ['linux', 'windows']
    else:
        os_types = ['darwin']

    cur_path = os.path.dirname(os.path.realpath(__file__))
    sdk_package_location_prefix = cur_path[0:cur_path.find('build')]
    sdk_package_directories = []

    for os_type in os_types:
        sdk_package_directories.append(os.path.join(sdk_package_location_prefix, sdk_package_location, os_type))
    for sdk_package_directory in sdk_package_directories: 
        if not os.path.exists(sdk_package_directory):
            raise Exception("Error: directory {} not exits!".format(sdk_package_directory))

    return sdk_package_directories


def get_all_sdk_package_list():
    global sdk_package_list
    compressed_file_dict = {}
    sdk_package_directories = get_sdk_package_directories()
    for sdk_package_directory in sdk_package_directories:
        for file_name in os.listdir(sdk_package_directory):
            if file_name.endswith(".zip") and file_name.find(sdk_version) != -1:
                compressed_file_dict.setdefault(sdk_package_directory, []).append(file_name)
        if sdk_package_directory in compressed_file_dict.keys():
            for compressed_file in compressed_file_dict[sdk_package_directory]:
                add_files_to_sdk_package(sdk_package_directory, compressed_file)
        else:
            raise Exception("Error: {} not in {}, please check.".format(sdk_package_directory, compressed_file_dict))

    return sdk_package_list


def get_redundant_set(sdk_check_list):
    outside_the_list_set = set()
    sdk_check_files, sdk_check_directories = parse_sdk_check_list(sdk_check_list)
    sdk_list_set = set(sdk_check_files)
    sym_intersection = sdk_package_set.symmetric_difference(sdk_list_set)
    remove_check_from_package_set = sdk_package_set.intersection(sym_intersection)
    sdk_directorys_tuple = tuple(map(str, sdk_check_directories))
    for file in remove_check_from_package_set:
        if not file.startswith(sdk_directorys_tuple):
            outside_the_list_set.add(file)

    return outside_the_list_set


def get_unpacked_directories(sdk_check_list):
    sdk_check_directories = parse_sdk_check_list(sdk_check_list)[1]
    sdk_check_directories_set = set(sdk_check_directories)
    for directory in sdk_check_directories: 
        for file in sdk_package_list:
            if file.startswith(directory):
                sdk_check_directories_set.discard(directory)
                break

    return sdk_check_directories_set


def get_missing_set(sdk_check_list):
    sdk_list_set = set(parse_sdk_check_list(sdk_check_list)[0])
    sym_intersection = sdk_package_set.symmetric_difference(sdk_list_set)
    missing_set = sdk_list_set.intersection(sym_intersection)
    sdk_unpacked_directories = get_unpacked_directories(sdk_check_list)
    if len(sdk_unpacked_directories) != 0:
        for directory in sdk_unpacked_directories:
            missing_set.add(directory)

    return missing_set


def output_the_verification_result(sdk_check_list):
    sdk_package_missing_set = get_missing_set(sdk_check_list)
    sdk_package_redundant_set = get_redundant_set(sdk_check_list)

    if len(sdk_package_missing_set) == 0 and len(sdk_package_redundant_set) == 0:
        print("package and verify successful!") 
    else:
        if len(sdk_package_missing_set) != 0 and len(sdk_package_redundant_set) != 0:
            print("SDK package is less than SDK delivery list, missing: {}.".format(sdk_package_missing_set))
            print("SDK package is more than SDK delivery list, extra: {}.".format(sdk_package_redundant_set))
            sys.exit(1)
        elif len(sdk_package_missing_set) != 0:
            print("SDK package is less than SDK delivery list, missing: {}.".format(sdk_package_missing_set))
            sys.exit(1)
        else:
            print("SDK package is more than SDK delivery list, extra: {}.".format(sdk_package_redundant_set))
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-delivery-list')
    parser.add_argument('root_build_dir')
    parser.add_argument('--sdk-archive-dir')
    parser.add_argument('product_name')
    parser.add_argument('sdk_version')
    options = parser.parse_args()

    sdk_check_list = options.sdk_delivery_list
    root_build_directory = options.root_build_dir[2:]
    global sdk_package_location
    sdk_package_location = os.path.join(root_build_directory, options.sdk_archive_dir)
    global product_name
    product_name = options.product_name
    global sdk_version
    sdk_version = options.sdk_version

    global sdk_package_set 
    sdk_package_set = set(get_all_sdk_package_list())
    output_the_verification_result(sdk_check_list)


if __name__ == '__main__':
    sys.exit(main())