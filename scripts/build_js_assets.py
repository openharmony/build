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
import tempfile
import json
import shutil

from util import build_utils  # noqa: E402


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--output', help='stamp file')
    parser.add_option('--js-assets-dir', help='js assets directory')
    parser.add_option('--nodejs-path', help='path to nodejs app')
    parser.add_option('--webpack-js', help='path to webpack.js')
    parser.add_option('--webpack-config-js', help='path to webpack.config.js')
    parser.add_option('--hap-profile', help='path to hap profile')
    parser.add_option('--build-mode', help='debug mode or release mode')

    options, _ = parser.parse_args(args)
    options.js_assets_dir = build_utils.parse_gn_list(options.js_assets_dir)
    return options


def build_ace(cmd, source, output, profile, mode):
    with build_utils.temp_dir() as build_dir:
        gen_dir = os.path.join(build_dir, 'gen')
        manifest = os.path.join(build_dir, 'manifest.json')
        my_env = {
            "aceModuleRoot": source,
            "aceModuleBuild": gen_dir,
            "aceManifestPath": manifest,
            "buildMode": mode,
            "PATH": os.environ.get('PATH'),
        }
        if not os.path.exists(manifest) and profile:
            with open(profile) as fp:
                build_utils.write_json(
                    json.load(fp)['module']['js'][0], manifest)
        build_utils.check_output(cmd, env=my_env)
        for root, _, files in os.walk(gen_dir):
            for file in files:
                filename = os.path.join(root, file)
                if filename.endswith('.js.map'):
                    os.unlink(filename)
        build_utils.zip_dir(output,
                            gen_dir,
                            zip_prefix_path='assets/js/default/')


def main(args):
    options = parse_args(args)

    inputs = ([
        options.nodejs_path, options.webpack_js, options.webpack_config_js
    ])
    depfiles = (build_utils.get_all_files(options.js_assets_dir[0]))

    cmd = [
        options.nodejs_path, options.webpack_js, '--config',
        options.webpack_config_js,
    ]

    build_utils.call_and_write_depfile_if_stale(
        lambda: build_ace(cmd, options.js_assets_dir[0], options.output,
                          options.hap_profile, options.build_mode),
        options,
        depfile_deps=depfiles,
        input_paths=depfiles + inputs,
        input_strings=cmd + [options.build_mode],
        output_paths=([options.output]),
        force=False,
        add_pydeps=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
