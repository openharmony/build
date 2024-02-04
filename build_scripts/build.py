#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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
#

import os
import sys
import importlib
import subprocess


def search(findir: str, target: str) -> str or bool:
    for root, _, files in os.walk(findir):
        if target in files:
            return root
    return False


def find_top() -> str:
    cur_dir = os.getcwd()
    while cur_dir != "/":
        build_config_file = os.path.join(
            cur_dir, 'build/config/BUILDCONFIG.gn')
        if os.path.exists(build_config_file):
            return cur_dir
        cur_dir = os.path.dirname(cur_dir)


def get_python(python_relative_dir: str) -> str:
    topdir = find_top()
    if python_relative_dir is None:
        python_relative_dir = 'prebuilts/python'
    python_base_dir = os.path.join(topdir, python_relative_dir)

    if os.path.exists(python_base_dir):
        python_dir = search(python_base_dir, 'python3')
        return os.path.join(python_dir, 'python3')
    else:
        print("please execute build/prebuilts_download.sh.",
            "if you used '--python-dir', check whether the input path is valid.")
        sys.exit()


def check_output(cmd: str, **kwargs) -> str:
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               **kwargs)
    for line in iter(process.stdout.readline, ''):
        sys.stdout.write(line)
        sys.stdout.flush()

    process.wait()
    ret_code = process.returncode

    return ret_code


def build(path: str, args_list: list) -> str:
    python_dir = None
    if "--python-dir" in args_list:
        index = args_list.index("--python-dir")
        if index < len(args_list) - 1:
            python_dir = args_list[index + 1]
            del args_list[index: index + 2]
        else:
            print("-python-dir parmeter missing value.")
            sys.exit()
    python_executable = get_python(python_dir)
    cmd = [python_executable, 'build/hb/main.py', 'build'] + args_list
    return check_output(cmd, cwd=path)


def main():
    root_path = find_top()
    return build(root_path, sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
