#!/usr/bin/env python
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

import optparse
import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from scripts.util import build_utils  # noqa: E402

def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--output', help='generated ndk stub file')
    parser.add_option('--headers',
                      action='append',
                      help='base directory of ndk common files')

    options, _ = parser.parse_args(args)

    return options

def check_ndk_header(headers, output):
    cmd_list=[]
    cmd_list.append('clang')
    cmd_list.append('-I sdk-native/os-irrelevant/sysroot/')
    cmd_list.append('-std=c99')
    for file in headers:
        command = cmd_list + [file]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            fs = open(r'Error.txt','a', encoding='utf-8')
            fs.write(f'Error: {result.stderr.decode()}')
            fs.close()
    
    build_utils.touch(output)


def main(args):
    options = parse_args(args)
    build_utils.call_and_write_depfile_if_stale(lambda: check_ndk_header(options.headers, options.output),
                                                options,
                                                output_paths=([options.output]),
                                                input_strings=args,
                                                force=False,
                                                add_pydeps=False)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
