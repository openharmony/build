#!/usr/bin/env python
# coding: utf-8
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
import argparse
import subprocess
import os


def args_parse(argv):
    parser = argparse.ArgumentParser(description='mkchip_ckm.py')

    parser.add_argument("--config-file-path", help="The source file for sload.")
    parser.add_argument("--src-dir", help="The source file for sload.")
    parser.add_argument("--device-name", help="The device for mkfs.")
    parser.add_argument("--mkextimage-tools-path", help="The device for mkfs.")
    parser.add_argument("--build-image-tools-path", nargs='*', help="The device for mkfs.")
    parser.add_argument("--root-config-list-json", help="The device for mkfs.")
    args = parser.parse_known_args(argv)[0]
    return args


def run_cmd(cmd: str):
    res = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    sout, serr = res.communicate()

    return res.pid, res.returncode, sout, serr


def make_vendor_package(args):
    src_dir = args.src_dir
    device_name = args.device_name
    mkextimage_tools_path = args.mkextimage_tools_path
    config_file_path = args.config_file_path
    mk_configs_raw = []
    with open(args.config_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            mk_configs_raw.append(line)
    mk_configs = " ".join(mk_configs_raw)
    mk_configs = " ".join([src_dir, device_name, mk_configs])
    res = run_cmd(" ".join([mkextimage_tools_path, mk_configs]))
    if res[1]:
        print("pid " + str(res[0]) + " ret " + str(res[1]) + "\n" +
                res[2].decode() + res[3].decode())
        sys.exit(2)


def build(args):
    args = args_parse(args)
    if args.build_image_tools_path:
        env_path = ':'.join(args.build_image_tools_path)
        os.environ['PATH'] = '{}:{}'.format(env_path, os.environ.get('PATH'))
    make_vendor_package(args)

if __name__ == '__main__':
    build(sys.argv[1:])
