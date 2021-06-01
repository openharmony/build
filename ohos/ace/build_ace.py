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

import optparse
import os
import sys
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from scripts.util import build_utils  # noqa: E402


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--output', help='stamp file')
    parser.add_option('--ace-loader-home', help='path to ace loader')
    parser.add_option(
        '--generated-asset-dir', help='directory of generated ace asset')
    parser.add_option('--source-dir', help='js source directory')
    parser.add_option('--nodejs', help='path to nodejs app')
    parser.add_option('--webpack-js', help='path to webpack.js')
    parser.add_option('--webpack-config-js', help='path to webpack.config.js')

    options, _ = parser.parse_args(args)
    return options


def build_ace(cmd, source_dir, output, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    with build_utils.temp_dir() as build:
        my_env = {
            "aceModuleRoot": source_dir,
            "aceModuleBuild": build,
            "PATH": os.environ.get('PATH'),
        }
        build_utils.check_output(cmd, env=my_env)
        shutil.copytree(build, output_dir)
        build_utils.touch(output)


def main(args):
    options = parse_args(args)

    depfile_deps = ([
        options.nodejs, options.webpack_js, options.webpack_config_js
    ])
    depfile_deps += (build_utils.get_all_files(options.source_dir))

    cmd = [
        options.nodejs, options.webpack_js, '--config',
        options.webpack_config_js
    ]

    build_utils.call_and_write_depfile_if_stale(
        lambda: build_ace(cmd,
                          options.source_dir,
                          options.output,
                          options.generated_asset_dir),
        options,
        depfile_deps=depfile_deps,
        input_paths=depfile_deps,
        input_strings=cmd + [options.generated_asset_dir],
        output_paths=([options.output, options.generated_asset_dir]),
        force=False,
        add_pydeps=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
