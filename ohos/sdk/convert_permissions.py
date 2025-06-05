#!/usr/bin/env python
# # -*- coding: utf-8 -*-
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
import shutil
import subprocess

INTERFACE_PATH = "interface/sdk-js"
API_PATH = "api"
API_GEN_PATH = "build-tools/api"
CONVERTER_DIR = "build-tools/permissions_converter"
CONVERTER_TOOL = "build-tools/permissions_converter/convert.js"


def copy_sdk_interface(source_root: str, project_path: str):
    source = os.path.join(source_root, INTERFACE_PATH)
    dest = os.path.join(source_root, project_path)
    if os.path.exists(dest) is False:
        shutil.copytree(source, dest)


def copy_api(source_root: str, project_path: str):
    source = os.path.join(source_root, project_path, API_PATH)
    dest = os.path.join(source_root, project_path, API_GEN_PATH)
    if os.path.exists(dest) is False:
        shutil.copytree(source, dest)


def convert_permission_method(source_root: str, project_path: str, file_name: str, nodejs: str):
    permission_convert_dir = os.path.join(INTERFACE_PATH, CONVERTER_DIR)
    permission_convert_tool = os.path.join(INTERFACE_PATH, CONVERTER_TOOL)
    config_file = os.path.join("base/security/access_token/services/accesstokenmanager", "permission_definitions.json")
    permission_gen_path = os.path.join(project_path, API_GEN_PATH, file_name)

    tool = os.path.abspath(os.path.join(source_root, permission_convert_tool))
    nodejs = os.path.abspath(nodejs)
    config = os.path.abspath(os.path.join(source_root, config_file))
    output_path = os.path.abspath(os.path.join(source_root, permission_gen_path))
    process = subprocess.Popen([nodejs, tool, config, output_path], shell=False,
                        cwd=os.path.abspath(os.path.join(source_root, permission_convert_dir)),
                        stdout=subprocess.PIPE)
    process.wait()


def replace_sdk_api_dir(source_root: str, project_path: str, file_name: str):
    source = os.path.join(source_root, project_path, API_GEN_PATH, file_name)
    dest = os.path.join(source_root, project_path, API_PATH, file_name)
    if os.path.exists(dest):
        os.remove(dest)
    shutil.copyfile(source, dest)


def parse_step(source_root: str, project_path: str, file_name: str, nodejs: str):
    copy_sdk_interface(source_root, project_path)
    copy_api(source_root, project_path)
    convert_permission_method(source_root, project_path, file_name, nodejs)
    replace_sdk_api_dir(source_root, project_path, file_name)


def convert_permissions(root_build_dir: str, project_path: str, file_name: str, node_js: str):
    parse_step(root_build_dir, project_path, file_name, node_js)
    
