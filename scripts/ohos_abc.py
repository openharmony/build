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

import argparse
import os
import sys
from util import build_utils


def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--es2abc', help='path to es2abc')
    parser.add_argument('--sources', nargs='+', help='path to .ts file')
    parser.add_argument('--outputs', help='path to .abc file')
    parser.add_argument('--merge-abc', action='store_true', help='merge abc')
    parser.add_argument('--module', action='store_false', help='module type')

    options = parser.parse_args(args)
    return options


def gen_abc(options):
    cmd = [os.path.join(options.es2abc, 'es2abc'), '--output', options.outputs]
    if options.merge_abc:
        cmd.extend(['--merge-abc'])
    if options.module:
        cmd.extend(['--module'])
    cmd.extend(options.sources)
    build_utils.check_output(cmd, env=None)


def main(args):
    options = parse_args(args)

    outputs = [options.outputs]

    es2abc_path = os.path.join(options.es2abc, 'es2abc')
    build_utils.call_and_write_depfile_if_stale(
        lambda: gen_abc(options),
        options,
        depfile_deps=([options.es2abc]),
        input_paths=(options.sources + [es2abc_path]),
        output_paths=(outputs),
        input_strings=args,
        force=False,
        add_pydeps=False
    )

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
