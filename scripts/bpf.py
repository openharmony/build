#!/usr/bin/env python
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
import sys

from util import build_utils


def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--clang-path', help='path to clang')
    parser.add_argument('--include-dirs', nargs='+', help='path to header files')
    parser.add_argument('--output-file', help='path to .o file')
    parser.add_argument('--input-file', nargs='+', help='path to .c file')

    options = parser.parse_args(args)
    return options

def bpf_compile(options, cmd):
    my_env = None
    for f in options.input_file:
        cmd.extend(['-c', f])
        cmd.extend(['-o', options.output_file])
        build_utils.check_output(cmd, env=my_env)
        
def main(args):
    options = parse_args(args)
    cmd = [options.clang_path]
    cmd.extend(['-v', '-g', '-c', '-O2', '-target', 'bpf'])
    for include_dir in options.include_dirs:
        cmd.extend(['-I', include_dir])

    outputs = [options.output_file]

    build_utils.call_and_write_depfile_if_stale(
        lambda: bpf_compile(options, cmd),
        options,
        depfile_deps=([options.clang_path]),
        input_paths=(options.input_file + [options.clang_path]),
        output_paths=(outputs),
        input_strings=cmd,
        force=False,
        add_pydeps=False
    )

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
