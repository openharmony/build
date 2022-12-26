#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


import argparse
import os
import subprocess
import sys


def do_strip(strip, output, unstripped_file, mini_debug):
    if strip:
        result = subprocess.call(
            [strip, '-o', output, unstripped_file])

    if mini_debug and not unstripped_file.endswith(".exe"):
        unstripped_libfile = os.path.abspath(unstripped_file)
        script_path = os.path.join(
            os.path.dirname(__file__), 'mini_debug_info.py')
        ohos_root_path = os.path.join(os.path.dirname(__file__), '../..')
        result = subprocess.call(
            ['python3', script_path, '--unstripped-path', unstripped_libfile, '--stripped-path', output,
            '--root-path', ohos_root_path])

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strip',
                        help='The strip binary to run',
                        metavar='FILE')
    parser.add_argument('--unstripped-file',
                        help='Binary file produced by linking command',
                        metavar='FILE')
    parser.add_argument('--output',
                        required=True,
                        help='Final output binary file',
                        metavar='FILE')
    parser.add_argument('command', nargs='+',
                        help='Linking command')
    parser.add_argument('--mini-debug',
                        action='store_true',
                        default=False,
                        help='Add .gnu_debugdata section for stripped sofile')
    args = parser.parse_args()

    return do_strip(args.strip, args.output, args.unstripped_file, args.mini_debug)


if __name__ == "__main__":
    sys.exit(main())
