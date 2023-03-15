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
import subprocess
import shutil
import json5

from util import build_utils
from util import file_utils


def parse_args(args):
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--npm', help='')
    parser.add_argument('--nodejs', help='')
    parser.add_argument('--cwd', help='')
    parser.add_argument('--app-profile', help='')
    parser.add_argument('--hap-profile', help='')
    parser.add_argument('--ohos-sdk-home', help='')
    parser.add_argument('--enable-debug', action='store_true', help='')
    parser.add_argument('--build-level', default='module', help='')
    parser.add_argument('--output-file', help='')
    parser.add_argument('--build-profile', help='')
    parser.add_argument('--system-lib-module-info-list', nargs='+', help='')
    parser.add_argument('--ohos-app-abi', help='')

    options = parser.parse_args(args)
    return options


def make_env(build_profile, cwd, npm):
    os.environ['PATH'] = '{}:{}'.format(npm, os.environ.get('PATH'))
    cur_dir = os.getcwd()
    with open(build_profile, 'r') as input_f:
        build_info = json5.load(input_f)
        modules_list = build_info.get('modules')
        os.chdir(cwd)
        npm_install_cmd = ['npm', 'install']
        subprocess.run(npm_install_cmd)
        for module in modules_list:
            src_path = module.get('srcPath')
            npm_install_path = os.path.join(cwd, src_path)
            os.chdir(npm_install_path)
            subprocess.run(npm_install_cmd)
    os.chdir(cur_dir)


def gen_unsigned_hap_path_json(build_profile, cwd):
    unsigned_hap_path_json = {}
    unsigned_hap_path_list = []
    with open(build_profile, 'r') as input_f:
        build_info = json5.load(input_f)
        modules_list = build_info.get('modules')
        for module in modules_list:
            src_path = module.get('srcPath')
            unsigned_hap_path = os.path.join(cwd, src_path, 'build/default/outputs/default')
            hap_file = build_utils.find_in_directory(unsigned_hap_path, '*unsigned.hap')
            unsigned_hap_path_list.extend(hap_file)
        unsigned_hap_path_json['unsigned_hap_path_list'] = unsigned_hap_path_list
    return unsigned_hap_path_json


def app_compile(options, cmd, my_cwd):
    my_env = {'OHOS_SDK_HOME': options.ohos_sdk_home}
    build_utils.check_output(cmd, cwd=my_cwd, env=my_env)


def copy_libs(cwd, system_lib_module_info_list, ohos_app_abi):
    for _lib_info in system_lib_module_info_list:
        lib_info = file_utils.read_json_file(_lib_info)
        lib_path = lib_info.get('source')
        if os.path.exists(lib_path):
            lib_name = os.path.basename(lib_path)
            dest = os.path.join(cwd, 'entry/libs', ohos_app_abi, lib_name)
            print('lijunru:dest:', dest)
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(lib_path, dest)


def main(args):
    options = parse_args(args)
    cwd = os.path.abspath(options.cwd)

    # copy system lib deps to app libs dir
    if options.system_lib_module_info_list:
        copy_libs(cwd, options.system_lib_module_info_list, options.ohos_app_abi)

    # generate unsigned_hap_path_list and run npm install
    make_env(options.build_profile, cwd, options.npm)
    depfiles = build_utils.get_all_files(cwd)
    os.environ['PATH'] = '{}:{}'.format(options.nodejs, os.environ.get('PATH'))
    cmd = ['node', './node_modules/@ohos/hvigor/bin/hvigor.js']
    cmd.extend(['clean', 'assembleHap', '--mode'])
    cmd.extend([options.build_level])
    cmd.extend(['-p'])
    if options.enable_debug:
        cmd.extend(['debuggable=true'])
    else:
        cmd.extend(['debuggable=false'])

    outputs = options.output_file

    build_utils.call_and_write_depfile_if_stale(
        lambda: app_compile(options, cmd, cwd),
        options,
        depfile_deps=depfiles,
        input_paths=depfiles,
        output_paths=(outputs),
        input_strings=cmd,
        force=False,
        add_pydeps=False
    )
    unsigned_hap_path_json = gen_unsigned_hap_path_json(options.build_profile, cwd)
    file_utils.write_json_file(options.output_file, unsigned_hap_path_json)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
