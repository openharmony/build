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
OUT_ROOT = "out/sdk-public"
OUTPATH = os.path.join(OUT_ROOT, "public_interface/sdk-js")
API_PATH = os.path.join(OUTPATH, "api")
API_GEN_PATH = os.path.join(OUTPATH, "build-tools/api")


def copy_sdk_interface(source_root):
    source = os.path.join(source_root, INTERFACE_PATH)
    dest = os.path.join(source_root, OUTPATH)
    if os.path.exists(dest) is False:
        shutil.copytree(source, dest)


def copy_api(source_root):
    source = os.path.join(source_root, API_PATH)
    dest = os.path.join(source_root, API_GEN_PATH)
    if os.path.exists(dest) is False:
        shutil.copytree(source, dest)


def convert_permission_method(source_root, nodejs):
    permission_convert_dir = os.path.join(OUTPATH, "build-tools", "permissions_converter")
    permission_convert_tool = os.path.join(permission_convert_dir, "convert.js")
    config_file = os.path.join("base/global/system_resources/systemres/main", "config.json")
    permission_gen_path = os.path.join(API_GEN_PATH, "permissions.d.ts")

    tool = os.path.abspath(os.path.join(source_root, permission_convert_tool))
    nodejs = os.path.abspath(nodejs)
    config = os.path.abspath(os.path.join(source_root, config_file))
    output_path = os.path.abspath(os.path.join(source_root, permission_gen_path))
    process = subprocess.Popen([nodejs, tool, config, output_path], shell=False,
                        cwd=os.path.abspath(os.path.join(source_root, permission_convert_dir)),
                        stdout=subprocess.PIPE)
    process.wait()


def replace_sdk_api_dir(source_root):
    source = os.path.join(source_root, API_GEN_PATH, "permissions.d.ts")
    dest = os.path.join(source_root, API_PATH, "permissions.d.ts")
    if os.path.exists(dest):
        os.remove(dest)
    shutil.copyfile(source, dest)


def parse_step(source_root, nodejs):
    copy_sdk_interface(source_root)
    copy_api(source_root)
    convert_permission_method(source_root, nodejs)
    replace_sdk_api_dir(source_root)


def convert_permissions(root_build_dir, node_js):
    parse_step(root_build_dir, node_js)
    
