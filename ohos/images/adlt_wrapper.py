#!/usr/bin/env python3
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


import sys
import os
import argparse
import subprocess
import shutil


def execute_adlt_command(args):
    cmd = [
        args.adlt_exe,
        f'--root-dir={args.adlt_root_dir}',
        '-o',
        args.output_file,
        args.allowed_lib_list,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    stdout, stderr = proc.communicate()
    for line in stdout.splitlines():
        print(f'[1/1] info: {line}')
    for line in stderr.splitlines():
        print(f'[1/1] warning: {line}')
    if proc.returncode:
        raise Exception(f'ReturnCode:{proc.returncode}. excute failed: {stderr}')


def remove_origin_lib(args):
    with open(args.allowed_lib_list, 'r') as f:
        lines = f.readlines()
    for line in lines:
        so_abspath = os.path.join(args.adlt_root_dir, line.strip("\n"))
        if os.path.exists(so_abspath):
            os.remove(so_abspath)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--adlt-exe', required=True, help='adlt exe path')
    parser.add_argument('--adlt-root-dir', required=True, help='adlt root dir')
    parser.add_argument('--allowed-lib-list', required=True, help='allowed lib list')
    parser.add_argument('--output-file', required=True, help='output file')
    args = parser.parse_args(argv)
    if not os.path.exists(args.output_file):
        execute_adlt_command(args)
        remove_origin_lib(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))