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

import argparse
import os
import sys
import shutil
import subprocess
from convert_permissions import convert_permissions

OUT_ROOT_LIST = ["dynamic/sdk-js",
                 "static/sdk-js"]
OUT_SDK_TYPE = ["ets", "ets2"]
OUT_PERMISSION_FILE = ["permissions.d.ts", "permissions.d.ets"]
INTERFACE_PATH = "interface/sdk-js"
OUT_ROOT = "out/sdk-public"
API_MODIFY_DIR = "build-tools"
API_MODIFY_TOOL = "delete_systemapi_plugin.js"
ETS_MODIFY_TOOL = "handleApiFiles.js"
CHECK_API_VERSION_TOOL = "checkApiVersion.js"
API_PATH = "api"
API_GEN_PATH = "build-tools/api"
KITS_PATH = "kits"
KITS_GEN_PATH = "build-tools/kits"
ARKTS_PATH = "arkts"
ARKTS_GEN_PATH = "build-tools/arkts"
PARSE_ETS2_API = "arkui_transformer"
PACKAGE_PATH = "build/arkui_transformer.js"
TYPE_MODIFY_TOOL = "intToNumber.js"
TYPE_CHANGE_DIR = "type-change"
TYPE_CHANGE_API_GEN_PATH = "build-tools/type-change/api"
TYPE_CHANGE_ARKTS_GEN_PATH = "build-tools/type-change/arkts"


def copy_sdk_interface(source_root: str, out_path: str):
    source = os.path.join(source_root, INTERFACE_PATH)
    dest = os.path.join(source_root, out_path)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def replace_sdk_dir(root_build_dir: str, from_path: str, to_path: str):
    dest = os.path.join(root_build_dir, to_path)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    source = os.path.join(root_build_dir, from_path)
    shutil.copytree(source, dest)


def copy_arkts_api_method(source_root: str, out_path: str, nodejs: str, sdk_type: str,  is_public: str):
    input_path = os.path.join(source_root, INTERFACE_PATH)
    input_path = os.path.abspath(input_path)
    output_path = os.path.join(source_root, out_path)
    output_path = os.path.abspath(output_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    tool = os.path.join(source_root, INTERFACE_PATH, API_MODIFY_DIR,
                        ETS_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    nodejs = os.path.abspath(nodejs)
    p = subprocess.Popen([nodejs, tool, "--path", input_path, "--output", output_path, "--type",
                          sdk_type, "--isPublic", is_public, "--create-keep-file", "true"], stdout=subprocess.PIPE)
    p.wait()


# API_LEVEL校验
def check_api_version_method(source_root: str, api_root: str, sdk_version: str, nodejs: str):
    input_path = os.path.join(source_root, api_root)
    input_path = os.path.abspath(input_path)
    tool = os.path.join(source_root, INTERFACE_PATH, API_MODIFY_DIR, CHECK_API_VERSION_TOOL)
    tool = os.path.abspath(tool)
    nodejs = os.path.abspath(nodejs)

    p = subprocess.Popen([nodejs, tool, "--path", input_path, "--versionNumber", sdk_version],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()
    check_result = stdout.decode()

    p.wait()

    # 创建转换表，过滤文本中的换行、空格等字符
    custom_rules = str.maketrans("", "", " \n\t\r")

    if check_result.translate(custom_rules) != "":
        raise ValueError(check_result)


def remove_system_api_method(source_root: str, out_path: str, nodejs: str, sdk_type: str, build_sdk_path: str):

    tool = os.path.join(source_root, INTERFACE_PATH, API_MODIFY_DIR, API_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    api_dir = os.path.join(source_root, out_path, API_PATH)
    api_dir = os.path.abspath(api_dir)
    api_out_dir = os.path.join(source_root, out_path, API_MODIFY_DIR)
    api_out_dir = os.path.abspath(api_out_dir)
    build_sdk_path = os.path.abspath(build_sdk_path)

    nodejs = os.path.abspath(nodejs)
    p = subprocess.Popen([nodejs, tool, "--input", api_dir, "--output",
                          api_out_dir, "--type", sdk_type, "--build-sdk-path", build_sdk_path], stdout=subprocess.PIPE)
    p.wait()


def change_int_to_number(source_root: str, out_path: str, nodejs: str, sdk_type: str):
    tool = os.path.join(source_root, INTERFACE_PATH,
                        API_MODIFY_DIR, TYPE_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    api_dir = os.path.join(source_root, out_path)
    api_dir = os.path.abspath(api_dir)
    api_out_dir = os.path.join(source_root, out_path, API_MODIFY_DIR, TYPE_CHANGE_DIR)
    api_out_dir = os.path.abspath(api_out_dir)

    nodejs = os.path.abspath(nodejs)
    process_list = []
    # 根据规格并发执行文本处理逻辑
    for index in range(10):
        process_list.append(subprocess.Popen([nodejs, tool, "--path", api_dir, "--output", api_out_dir, "--index",
                          str(index)], stdout=subprocess.PIPE))

    for process_obj in process_list:
        process_obj.wait()


def parse_step(options):
    for i, out_path in enumerate(OUT_ROOT_LIST):
        sdk_type = OUT_SDK_TYPE[i]
        permission_file = OUT_PERMISSION_FILE[i]
        out_path = os.path.join(options.output_interface_sdk, out_path)
        out_path = os.path.relpath(out_path, options.root_build_dir)
        copy_arkts_api_method(options.root_build_dir, out_path, options.node_js, sdk_type, options.sdk_build_public)

        # 转换sdk_check_level为数值int类型，防止传入有误参数
        sdk_check_version = 0
        try:
            sdk_check_version = int(options.sdk_check_level)
        except BaseException as e:
            raise ValueError("sdk_check_level数值有误，请传入正确数值")
        if sdk_type == "ets" and sdk_check_version != 0:
            # 仅在编译dynamic时校验API版本
            check_api_version_method(options.root_build_dir, out_path, options.sdk_api_version, options.node_js)

        if options.sdk_build_public == "true":
            remove_system_api_method(
                options.root_build_dir, out_path, options.node_js, sdk_type, options.build_sdk_path)
            replace_sdk_dir(options.root_build_dir, os.path.join(
                out_path, API_GEN_PATH), os.path.join(out_path, API_PATH))
            replace_sdk_dir(options.root_build_dir, os.path.join(
                out_path, KITS_GEN_PATH), os.path.join(out_path, KITS_PATH))
            replace_sdk_dir(options.root_build_dir, os.path.join(
                out_path, ARKTS_GEN_PATH), os.path.join(out_path, ARKTS_PATH))

        convert_permissions(options.root_build_dir, out_path,
                            permission_file, options.node_js)

        if sdk_type == "ets":
            change_int_to_number(
                options.root_build_dir, out_path, options.node_js, sdk_type)
            replace_sdk_dir(options.root_build_dir, os.path.join(
                out_path, TYPE_CHANGE_API_GEN_PATH), os.path.join(out_path, API_PATH))
            replace_sdk_dir(options.root_build_dir, os.path.join(
                out_path, TYPE_CHANGE_ARKTS_GEN_PATH), os.path.join(out_path, ARKTS_PATH))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root-build-dir', required=True)
    parser.add_argument('--node-js', required=True)
    parser.add_argument('--sdk-build-public', required=True)
    parser.add_argument('--sdk-build-arkts', required=True)
    parser.add_argument('--npm-path', required=True)
    parser.add_argument('--output-interface-sdk', required=True)
    parser.add_argument('--build-sdk-path', required=True)
    parser.add_argument('--sdk-check-level', required=True)
    parser.add_argument('--sdk-api-version', required=True)

    options = parser.parse_args()

    parse_step(options)


if __name__ == '__main__':
    sys.exit(main())
