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
import re

from util import build_utils


def debug_log(*args, **kwargs):
    if os.getenv("IDLIZE_DEBUG") == "1":
        print(*args, **kwargs)


def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--nodejs')
    parser.add_argument('--arkgen-path')
    parser.add_argument(
        '--execute-mode', choices=['generate', 'scancpp', 'scanidl'])
    parser.add_argument('--generate-mode', choices=['dts2peer', 'idl2peer'])
    parser.add_argument('--input-dir', metavar='<path>')
    parser.add_argument('--input-files', nargs="+")
    parser.add_argument('--output-dir', metavar='<path>')
    parser.add_argument('--origin-dir', metavar='<path>')
    parser.add_argument('--input-file', metavar='<name>')
    parser.add_argument('--language', choices=['arkts', 'ts'])
    parser.add_argument('--generator-target', choices=['ohos'])
    parser.add_argument('--dir-mode', choices=['error', 'backup', 'delete'])
    parser.add_argument('--default-idl-package')

    options = parser.parse_args(args)
    return options


def get_generate_mode(options):
    generate_mode = ""
    if options.generate_mode == "dts2peer":
        generate_mode = "--dts2peer"
    elif options.generate_mode == "idl2peer":
        generate_mode = "--idl2peer"
    return generate_mode


def handle_target_path(options):
    target_path = options.output_dir + "/generated"
    if os.path.exists(target_path):
        match options.dir_mode:
            case 'delete':
                shutil.rmtree(target_path)
            case 'backup':
                shutil.move(target_path, target_path + ".bak")
            case _:
                raise ValueError(
                    "Target dir {} already exist!".format(target_path))


def handle_input(run_config, options):
    if options.input_dir:
        run_config += ["--input-dir", options.input_dir]
    elif options.input_files:
        run_config += ["--input-files", *options.input_files]


def pack_run_config(options):
    handle_target_path(options)
    run_config = [options.nodejs, options.arkgen_path]
    run_config += [get_generate_mode(options)]
    handle_input(run_config, options)
    run_config += ["--output-dir", options.output_dir]
    run_config += ["--language", options.language]
    run_config += ["--verify-idl", "--docs=none"]
    run_config += ["--default-idl-package", options.default_idl_package]
    run_config += ["--use-new-ohos"]
    return run_config


def generate(options):
    debug_log("idlize generate", options)
    run_config = pack_run_config(options)
    debug_log("idlize generate run_config", run_config)
    try:
        process = subprocess.Popen(
            run_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        _, stderr = process.communicate()

        if process.returncode == 0:
            print("idlize argen genereate succuess")
        else:
            print("idlize argen genereate failed")
            print(stderr)
            sys.exit(1)
    except Exception as e:
        print("idlize argen genereate error")
        print(e)
        sys.exit(1)


def scan(scandir, origindir, pattern):
    result_files = []
    for root, _, files in os.walk(scandir):
        for file in files:
            if re.match(pattern, file):
                result_files.append(
                    origindir + "/" + os.path.relpath(os.path.join(root, file), scandir))
    for file in result_files:
        print(file)


def main(args):
    options = parse_args(args)
    if options.execute_mode == "generate":
        generate(options)
    elif options.execute_mode == "scancpp":
        scan(options.output_dir, options.origin_dir,
             r"(?i)^(?!.*impl).*\.(cc|cpp)$")
    elif options.execute_mode == "scanidl":
        scan(options.input_dir, options.origin_dir,
             r"(?i).*\.idl$")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
