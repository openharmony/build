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
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file

OUT_ROOT_LIST = ["ets1.1/sdk-js",
                 "ets1.2/sdk-js"]
OUT_SDK_TYPE = ["ets", "ets2"]
OUT_PERMISSION_FILE = ["permissions.d.ts", "permissions.d.ets"]
INTERFACE_PATH = "interface/sdk-js"
OUT_ROOT = "out/sdk-public"
API_MODIFY_DIR = "build-tools"
API_MODIFY_TOOL = "delete_systemapi_plugin.js"
ETS_MODIFY_TOOL = "handleApiFiles.js"
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


def copy_arkts_api_method(source_root: str, out_path: str, nodejs: str, sdk_type: str, is_public: str):
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
    p = subprocess.Popen([nodejs, tool, "--path", input_path, "--output",
                         output_path, "--type", sdk_type, "--isPublic", is_public], stdout=subprocess.PIPE)
    p.wait()


def remove_system_api_method(source_root: str, out_path: str, nodejs: str, sdk_type: str):

    tool = os.path.join(source_root, INTERFACE_PATH, API_MODIFY_DIR, API_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    api_dir = os.path.join(source_root, out_path, API_PATH)
    api_dir = os.path.abspath(api_dir)
    api_out_dir = os.path.join(source_root, out_path, API_MODIFY_DIR)
    api_out_dir = os.path.abspath(api_out_dir)

    nodejs = os.path.abspath(nodejs)
    p = subprocess.Popen([nodejs, tool, "--input", api_dir, "--output",
                          api_out_dir, "--type", sdk_type], stdout=subprocess.PIPE)
    p.wait()


def compile_package(options, out_path: str):
    tool_path = os.path.abspath(os.path.join(options.root_build_dir, INTERFACE_PATH, API_MODIFY_DIR, PARSE_ETS2_API))
    npm = os.path.abspath(options.npm_path)
    package_path = os.path.abspath(os.path.join(tool_path, PACKAGE_PATH))
    nodejs = os.path.abspath(options.node_js)
    input_dir = os.path.abspath(os.path.join(options.root_build_dir, out_path, "api/@internal/component/ets"))
    output = os.path.abspath(os.path.join(options.output_interface_sdk, "arkui_transformer_api"))
    custom_env = {
        'PATH': f"{os.path.dirname(os.path.abspath(options.node_js))}:{os.environ.get('PATH')}",
        'NODE_HOME': os.path.dirname(os.path.abspath(options.node_js)),
    }

    process = subprocess.run([npm, "run", "compile:arkui"], env=custom_env, cwd=tool_path, shell=False)

    if os.path.exists(package_path):
        p = subprocess.run([nodejs, package_path, "--input-dir", input_dir, "--target-dir", output], cwd=tool_path,
                           shell=False)
    else:
        print("arkui_transformer: tool path does not exist")

    return process


def regenerate_sdk_config_file(sdk_build_arkts: str, sdk_description_file: str,
                               output_sdk_desc_file: str):
    info_list = read_json_file(sdk_description_file)
    if sdk_build_arkts != "true":
        arkts_sdk_info_list = []
        for info in info_list:
            install_label_str = str(info.get("install_dir"))
            if install_label_str.startswith("ets/ets1.2/"):
                continue
            elif install_label_str.startswith("ets/ets1.1/build-tools/ets1.1interop"):
                continue
            elif install_label_str.startswith("ets/ets1.1/"):
                info["install_dir"] = str(info.get("install_dir")).replace("ets/ets1.1/", "ets/")
            arkts_sdk_info_list.append(info)
    else:
        arkts_sdk_info_list = info_list
    write_json_file(output_sdk_desc_file, arkts_sdk_info_list)
    

def change_int_to_number(source_root: str, out_path: str, nodejs: str, sdk_type: str):

    tool = os.path.join(source_root, INTERFACE_PATH,
                        API_MODIFY_DIR, TYPE_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    api_dir = os.path.join(source_root, out_path)
    api_dir = os.path.abspath(api_dir)
    api_out_dir = os.path.join(source_root, out_path, API_MODIFY_DIR, TYPE_CHANGE_DIR)
    api_out_dir = os.path.abspath(api_out_dir)

    nodejs = os.path.abspath(nodejs)
    p = subprocess.Popen([nodejs, tool, "--path", api_dir, "--output",
                          api_out_dir], stdout=subprocess.PIPE)
    p.wait()


def parse_step(options):
    for i, out_path in enumerate(OUT_ROOT_LIST):
        sdk_type = OUT_SDK_TYPE[i]
        permission_file = OUT_PERMISSION_FILE[i]
        out_path = os.path.join(options.output_interface_sdk, out_path)
        out_path = os.path.relpath(out_path, options.root_build_dir)
        copy_arkts_api_method(options.root_build_dir, out_path, options.node_js, sdk_type, options.sdk_build_public)

        if options.sdk_build_public == "true":
            remove_system_api_method(
                options.root_build_dir, out_path, options.node_js, sdk_type)
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

        if sdk_type == "ets2":
            compile_package(options, out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-description-file', required=True)
    parser.add_argument('--root-build-dir', required=True)
    parser.add_argument('--node-js', required=True)
    parser.add_argument('--output-arkts-sdk-desc-file', required=True)
    parser.add_argument('--sdk-build-public', required=True)
    parser.add_argument('--sdk-build-arkts', required=True)
    parser.add_argument('--npm-path', required=True)
    parser.add_argument('--output-interface-sdk', required=True)

    options = parser.parse_args()

    regenerate_sdk_config_file(options.sdk_build_arkts, options.sdk_description_file,
                               options.output_arkts_sdk_desc_file)

    parse_step(options)


if __name__ == '__main__':
    sys.exit(main())
