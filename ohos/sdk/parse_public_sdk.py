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
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file

INTERFACE_PATH = "interface/sdk-js"
OUT_ROOT = "out/sdk-public"
OUTPATH = os.path.join(OUT_ROOT, "public_interface/sdk-js")
API_MODIFY_DIR = os.path.join(OUTPATH, "build-tools")
API_MODIFY_TOOL = os.path.join(API_MODIFY_DIR, "delete_systemapi_plugin.js")
API_PATH = os.path.join(OUTPATH, "api")
API_GEN_PATH = os.path.join(OUTPATH, "build-tools/api")
DEL_TARGET = ["//interface/sdk-js:bundle_api"]


def copy_sdk_interface(source_root):
    source = os.path.join(source_root, INTERFACE_PATH)
    dest = os.path.join(source_root, OUTPATH)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def replace_sdk_api_dir(source_root):
    dest = os.path.join(source_root, API_PATH)
    if os.path.exists:
        shutil.rmtree(dest)
    source = os.path.join(source_root, API_GEN_PATH)
    shutil.copytree(source, dest)


def remove_system_api_method(source_root, nodejs):
    tool = os.path.join(source_root, API_MODIFY_TOOL)
    tool = os.path.abspath(tool)
    nodejs = os.path.abspath(nodejs)
    cmd = "{} {}".format(nodejs, tool)
    p = subprocess.Popen(cmd, shell=True,
                        cwd=os.path.abspath(os.path.join(source_root, API_MODIFY_DIR)),
                        stdout=subprocess.PIPE)
    p.wait()

def regenerate_sdk_description_file(source_root, sdk_description_file, output_pub_sdk_desc_file):
    info_list = read_json_file(sdk_description_file)
    public_info_list = []
    for info in info_list:
        label = str(info.get("module_label"))
        if label in DEL_TARGET:
            continue
        if label.startswith("//{}".format(INTERFACE_PATH)):
            label = label.replace(INTERFACE_PATH, os.path.join(OUT_ROOT, "public_interface/sdk-js"))
            info["module_label"] = label
        public_info_list.append(info)
    write_json_file(output_pub_sdk_desc_file, public_info_list)


def parse_step(sdk_description_file, source_root, nodejs, output_pub_sdk_desc_file):
    copy_sdk_interface(source_root)
    remove_system_api_method(source_root, nodejs)
    replace_sdk_api_dir(source_root)
    regenerate_sdk_description_file(source_root, sdk_description_file, output_pub_sdk_desc_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-description-file', required=True)
    parser.add_argument('--root-build-dir', required=True)
    parser.add_argument('--node-js', required=True)
    parser.add_argument('--output-pub-sdk-desc-file', required=True)

    options = parser.parse_args()
    parse_step(options.sdk_description_file, options.root_build_dir,
            options.node_js, options.output_pub_sdk_desc_file)


if __name__ == '__main__':
    sys.exit(main())
