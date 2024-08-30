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

import sys
import shutil
import argparse
import subprocess
import os


def copy_strip(args):
    shutil.copy(args.input, args.output)
    subprocess.call([args.strip, args.output], shell=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--strip', required=True)
    parser.add_argument('--mini-debug', required=False)
    args = parser.parse_args()
    copy_strip(args)
    if args.mini_debug == "true":
        ohos_root_path = os.path.join(os.path.dirname(__file__), '../../..')
        script_path = os.path.join(os.path.dirname(__file__), '../../../build/toolchain/mini_debug_info.py')
        clang_base_path = os.path.join(os.path.dirname(__file__), '../../../prebuilts/clang/ohos')
        subprocess.call(
                ['python3', script_path, '--unstripped-path', args.input, '--stripped-path', args.output,
                '--root-path', ohos_root_path, '--clang-base-dir', clang_base_path])
    return 0

if __name__ == '__main__':
    sys.exit(main())
