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
import sys
import subprocess
import os
import json
import shutil

from util import build_utils

def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--nodejs', help='nodejs path')
    parser.add_argument('--arkgen-path', help='arkgen path')
    parser.add_argument('--execute-mode', choices=['generate', 'scan'])
    parser.add_argument('--generate-mode', choices=['dts2peer', 'idl2peer'])
    parser.add_argument('--input-dir', metavar='<path>', help='Path to input dir(s), comma separated')
    parser.add_argument('--output-dir', metavar='<path>', help='Path to output dir')
    parser.add_argument('--origin-dir', metavar='<path>')
    parser.add_argument('--input-file', metavar='<name>', help='Name of file to convert, all files in input-dir if none')
    parser.add_argument('--language', choices=['arkts', 'ts'], help='Output language')
    parser.add_argument('--generator-target', choices=['ohos'])
    parser.add_argument('--dir-mode', choices=['error', 'backup', 'delete'])

    options = parser.parse_args(args)
    return options

def generate(options):
    print("idlize generate", options)
    node_binary = options.nodejs
    generate_mode = ""
    if options.generate_mode == "dts2peer":
        generate_mode = "--dts2peer"
    elif options.generate_mode == "idl2peer":
        generate_mode = "--idl2peer"
    target_path = options.output_dir + "/generated"
    if os.path.exists(target_path):
        match options.dir_mode:
            case 'error':
                raise ValueError("Target dir {} already exist!".format(target_path))
            case 'backup':
                shutil.move(target_path, target_path + ".bak")
            case _:
                shutil.rmtree(target_path)
    run_config = [node_binary, options.arkgen_path, "--generator-target", options.generator_target, generate_mode, "--input-dir", options.input_dir, "--output-dir", options.output_dir, "--verify-idl", "--common-to-attributes", "--docs=none", "--language", options.language]
    print("idlize generate run_config", run_config)
    subprocess.run(run_config)

def scan(options):
    cpp_files = []
    for root, _, files in os.walk(options.output_dir):
        for file in files:
            if file.endswith(".cpp") or file.endswith(".cc"):
                cpp_files.append(options.origin_dir + "/" + os.path.relpath(os.path.join(root, file), options.output_dir))
    return cpp_files

def main(args):
    options = parse_args(args)
    if options.execute_mode == "generate":
        generate(options)
    elif options.execute_mode == "scan":
        cpp_files = scan(options)
        for file in cpp_files:
            print(file)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))