#!/usr/bin/env python
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
import copy
import os
import shutil
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file  # noqa: E402

target_data_dict = dict()


def get_value_from_file(file, target, key, must=True):
    target_name = target[0]
    target_out_dir = target[1]
    file_path = os.path.join(target_out_dir, target_name + "_" + file + ".json")

    global target_data_dict
    target_data = target_data_dict.get(file_path)
    if target_data is not None:
        return target_data.get(key)

    if not os.path.exists(file_path):
        if must:
            raise Exception("File " + file_path + " not exists!")
        else:
            print(file_path + " not exists!")
            return "Unknown"

    target_data = read_json_file(file_path)
    target_data_dict[file_path] = target_data
    return target_data.get(key)


def get_valid_deps(module_deps, finish_list):
    already_check = []
    valid_list = []
    while len(module_deps) > 0:
        module_deps_copy = copy.deepcopy(module_deps)
        module_deps = []
        for module_dep in module_deps_copy:
            target_name = module_dep.get("target_name")
            target_out_dir = module_dep.get("target_out_dir")

            element = (target_name, target_out_dir)
            if already_check.count(element) > 0:
                continue
            already_check.append(element)

            target_type = get_value_from_file("deps_data", element, "type", False)
            if target_type == "Unknown":
                continue
            elif target_type == "shared_library" or target_type == "etc":
                if finish_list.count(element) > 0:
                    continue
                valid_list.append(element)
            else:
                deps = get_value_from_file("deps_data", element, "module_deps_info", False)
                for dep in deps:
                    name = dep.get("target_name")
                    out_dir = dep.get("target_out_dir")
                    dep_tup = (name, out_dir)
                    module_deps.append(dep)
    return valid_list


def check_debug_info(check_file, readelf):
    out = subprocess.Popen([readelf, "-S", check_file], shell=False, stdout=subprocess.PIPE)
    infos = out.stdout.read().splitlines()
    for info in infos:
        info_str = info.decode()
        pos = info_str.find(".debug_info")
        if pos >= 0:
            return True
    return False


def do_check(target_out_dir, target_name, stripped_dir, readelf, abidiff, abidw, abi_dumps_path):
    element = (target_name, target_out_dir)
    prebuilt = get_value_from_file("deps_data", element, "prebuilt")
    if prebuilt:
        check_file = get_value_from_file("deps_data", element, "source_path")
        if not os.path.exists(check_file):
            raise Exception("File " + check_file + " not exists!")
        has_debug_info = check_debug_info(check_file, readelf)
        if not has_debug_info:
            raise Exception("Prebuilt target should be with debug info!")
    else:
        source = get_value_from_file("module_info", element, "source")
        check_file = os.path.join(stripped_dir, source)
        if not os.path.exists(check_file):
            raise Exception("File " + check_file + " not exists!")

    out_file = os.path.join(target_out_dir, target_name + "_abi_info.dump")
    ret = subprocess.call([abidw, "--out-file", out_file, check_file])
    if ret != 0:
        raise Exception("Execute abidw failed! Return value: " + str(ret))

    toolchain = get_value_from_file("deps_data", element, "toolchain")
    toolchain_name = toolchain.split(':')[-1]

    base_name = os.path.basename(out_file)
    base_file = os.path.join(abi_dumps_path, toolchain_name, base_name)
    if not os.path.exists(base_file):
        raise Exception("File " + base_file + " not exists!")
    ret = subprocess.call([abidiff, out_file, base_file])
    if ret != 0:
        raise Exception("ABI info in " + out_file + " and " + base_file + " are different!")


def get_copy_source_path(element):
    prebuilt = get_value_from_file("deps_data", element, "prebuilt")
    if prebuilt:
        source = get_value_from_file("deps_data", element, "output_path")
    else:
        source = get_value_from_file("module_info", element, "source")
    return (element, source)


def traverse_and_check(check_list, readelf, abidiff, abidw, abi_dumps_path):
    copy_list = []
    finish_list = []
    loop_count = 0
    while len(check_list) > 0:
        check_list_copy = copy.deepcopy(check_list)
        check_list = []
        for element in check_list_copy:
            if finish_list.count(element) > 0:
                continue
            finish_list.append(element)

            target_name = element[0]
            target_out_dir = element[1]
            target_type = get_value_from_file("deps_data", element, "type")
            if target_type == "etc":
                copy_list.append(copy.deepcopy(get_copy_source_path(element)))
                continue

            stable = get_value_from_file("deps_data", element, "stable")
            if not stable:
                if loop_count == 0:
                    raise Exception("Target '{}' is not stable! Check config in gn".format(target_name))
                else:
                    copy_list.append(copy.deepcopy(get_copy_source_path(element)))
                module_deps = get_value_from_file("deps_data", element, "module_deps_info")
                check_list.extend(get_valid_deps(module_deps, finish_list))
            else:
                stripped_dir = ""
                if target_type == "shared_library":
                    stripped_dir = "lib.unstripped"
                elif target_type == "executable":
                    stripped_dir = "exe.unstripped"
                else:
                    raise Exception("Invalid target type: '{}'".format(target_type))

                do_check(target_out_dir, target_name, stripped_dir, readelf, abidiff, abidw, abi_dumps_path)
                if loop_count == 0:
                    copy_list.append(copy.deepcopy(get_copy_source_path(element)))

                    module_deps = get_value_from_file("deps_data", element, "module_deps_info")
                    check_list.extend(get_valid_deps(module_deps, finish_list))
        loop_count += 1
    return copy_list


def get_copy_output_path(element, parent_output):
    output_path = parent_output
    target_type = get_value_from_file("deps_data", element, "type")
    if target_type == "etc":
        output_path = os.path.join(parent_output, "etc")
    elif target_type == "executable":
        output_path = os.path.join(parent_output, "bin")
    elif target_type == "shared_library":
        output_path = os.path.join(parent_output, get_value_from_file("module_info", element, "type"))
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clang-readelf', required=True)
    parser.add_argument('--target-out-dir', required=True)
    parser.add_argument('--check-datas-file', required=True)
    parser.add_argument('--abidiff-target-name', required=True)
    parser.add_argument('--abidiff-target-out-dir', required=True)
    parser.add_argument('--abidw-target-name', required=True)
    parser.add_argument('--abidw-target-out-dir', required=True)
    parser.add_argument('--abi-dumps-path', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.check_datas_file):
        raise Exception("File " + args.check_datas_file + " not exists!")

    abidiff_element = (args.abidiff_target_name, args.abidiff_target_out_dir)
    abidiff_bin = get_value_from_file("module_info", abidiff_element, "source")
    abidw_element = (args.abidw_target_name, args.abidw_target_out_dir)
    abidw_bin = get_value_from_file("module_info", abidw_element, "source")

    parent_output = os.path.join(args.target_out_dir, "module_package", "img_input")
    if not os.path.exists(parent_output):
        os.makedirs(parent_output, exist_ok=True)

    check_list = []
    check_datas = read_json_file(args.check_datas_file)
    for check_data in check_datas:
        element = (check_data.get("target_name"), check_data.get("target_out_dir"))
        check_list.append(element)

    copy_list = traverse_and_check(check_list, args.clang_readelf, abidiff_bin, abidw_bin, args.abi_dumps_path)
    for copy_element in copy_list:
        print("copy_list: '{}'".format(str(copy_element)))
        output = get_copy_output_path(copy_element[0], parent_output)
        if not os.path.exists(output):
            os.makedirs(output)
        if isinstance(copy_element[1], list):
            for file in copy_element[1]:
                shutil.copy(file, output)
        else:
            shutil.copy(copy_element[1], output)
    os.remove(args.check_datas_file)


if __name__ == '__main__':
    sys.exit(main())
