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

    parser.add_argument('--nodejs', help='nodejs path')
    parser.add_argument('--cwd', help='app project directory')
    parser.add_argument('--sdk-home', help='sdk home')
    parser.add_argument('--enable-debug', action='store_true', help='if enable debuggable')
    parser.add_argument('--build-level', default='project', help='module or project')
    parser.add_argument('--assemble-type', default='assembleApp', help='assemble type')
    parser.add_argument('--output-file', help='output file')
    parser.add_argument('--build-profile', help='build profile file')
    parser.add_argument('--system-lib-module-info-list', nargs='+', help='system lib module info list')
    parser.add_argument('--ohos-app-abi', help='ohos app abi')
    parser.add_argument('--ohpm-registry', help='ohpm registry', nargs='?')
    parser.add_argument('--hap-out-dir', help='hap out dir')
    parser.add_argument('--hap-name', help='hap name')
    parser.add_argument('--test-hap', help='build ohosTest if enable', action='store_true')
    parser.add_argument('--test-module', help='specify the module within ohosTest', default='entry')
    parser.add_argument('--module-libs-dir', help='', default='entry')
    parser.add_argument('--sdk-type-name', help='sdk type name', nargs='+', default=['sdk.dir'])

    options = parser.parse_args(args)
    return options


def make_env(build_profile, cwd, ohpm_registry):
    '''
    Set up the application compilation environment and run "ohpm install"
    :param build_profile: module compilation information file
    :param cwd: app project directory
    :param ohpm_registry: ohpm registry
    :return: None
    '''
    cur_dir = os.getcwd()
    with open(build_profile, 'r') as input_f:
        build_info = json5.load(input_f)
        modules_list = build_info.get('modules')
        ohpm_install_cmd = ['ohpm', 'install']
        if ohpm_registry:
            ohpm_install_cmd.append('--registry=' + ohpm_registry)
        os.chdir(cwd)
        if os.path.exists(os.path.join(cwd, 'oh_modules')):
            shutil.rmtree(os.path.join(cwd, 'oh_modules'))
        subprocess.run(['chmod', '+x', 'hvigorw'])
        if os.path.exists(os.path.join(cwd, '.arkui-x/android/gradlew')):
            subprocess.run(['chmod', '+x', '.arkui-x/android/gradlew'])

        proc = subprocess.Popen(ohpm_install_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding='utf-8')
        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise Exception('ReturnCode:{}. ohpm install failed. {}'.format(
                proc.returncode, stderr))

        for module in modules_list:
            src_path = module.get('srcPath')
            ohpm_install_path = os.path.join(cwd, src_path)
            if os.path.exists(os.path.join(ohpm_install_path, 'oh_modules')):
                shutil.rmtree(os.path.join(ohpm_install_path, 'oh_modules'))
            proc = subprocess.Popen(ohpm_install_cmd,
                                    cwd=ohpm_install_path,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    encoding='utf-8')
            stdout, stderr = proc.communicate()
            if proc.returncode:
                raise Exception('ReturnCode:{}. ohpm install module failed. {}'.format(
                    proc.returncode, stderr))
    os.chdir(cur_dir)


def gen_unsigned_hap_path_json(build_profile, cwd, options):
    '''
    Generate unsigned_hap_path_list
    :param build_profile: module compilation information file
    :param cwd: app project directory
    :return: None
    '''
    unsigned_hap_path_json = {}
    unsigned_hap_path_list = []
    with open(build_profile, 'r') as input_f:
        build_info = json5.load(input_f)
        modules_list = build_info.get('modules')
        for module in modules_list:
            src_path = module.get('srcPath')
            if options.test_hap:
                unsigned_hap_path = os.path.join(
                    cwd, src_path, 'build/default/outputs/ohosTest')
            else:
                unsigned_hap_path = os.path.join(
                    cwd, src_path, 'build/default/outputs/default')
            hap_file = build_utils.find_in_directory(
                unsigned_hap_path, '*-unsigned.hap')
            unsigned_hap_path_list.extend(hap_file)
        unsigned_hap_path_json['unsigned_hap_path_list'] = unsigned_hap_path_list
    file_utils.write_json_file(options.output_file, unsigned_hap_path_json)


def copy_libs(cwd, system_lib_module_info_list, ohos_app_abi, module_libs_dir):
    '''
    Obtain the output location of system library .so by reading the module compilation information file,
    and copy it to the app project directory
    :param cwd: app project directory
    :param system_lib_module_info_list: system library module compilation information file
    :param ohos_app_abi: app abi
    :return: None
    '''
    for _lib_info in system_lib_module_info_list:
        lib_info = file_utils.read_json_file(_lib_info)
        lib_path = lib_info.get('source')
        if os.path.exists(lib_path):
            lib_name = os.path.basename(lib_path)
            dest = os.path.join(cwd, f'{module_libs_dir}/libs', ohos_app_abi, lib_name)
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(lib_path, dest)


def hvigor_build(cwd, options):
    '''
    Run hvigorw to build the app or hap
    :param cwd: app project directory
    :param options: command line parameters
    :return: None
    '''
    if options.test_hap:
        cmd = ['bash', './hvigorw', '--mode', 'module', '-p',
               f'module={options.test_module}@ohosTest', 'assembleHap']
    else:
        cmd = ['bash', './hvigorw', '--mode',
               options.build_level, '-p', 'product=default', options.assemble_type]
    if options.enable_debug:
        cmd.extend(['-p', 'debuggable=true'])
    else:
        cmd.extend(['-p', 'debuggable=false'])

    sdk_dir = options.sdk_home
    nodejs_dir = os.path.abspath(
        os.path.dirname(os.path.dirname(options.nodejs)))

    with open(os.path.join(cwd, 'local.properties'), 'w') as f:
        for sdk_type in options.sdk_type_name:
            f.write(f'{sdk_type}={sdk_dir}\n')
        f.write(f'nodejs.dir={nodejs_dir}\n')
    subprocess.run(['bash', './hvigorw', 'clean'], cwd=cwd)
    proc = subprocess.Popen(cmd, 
                            cwd=cwd, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='utf-8')
    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise Exception('ReturnCode:{}. Hvigor build failed: {}'.format(proc.returncode, stderr))


def main(args):
    options = parse_args(args)
    cwd = os.path.abspath(options.cwd)

    # copy system lib deps to app libs dir
    if options.system_lib_module_info_list:
        copy_libs(cwd, options.system_lib_module_info_list,
                  options.ohos_app_abi, options.module_libs_dir)

    os.environ['PATH'] = '{}:{}'.format(os.path.dirname(
        os.path.abspath(options.nodejs)), os.environ.get('PATH'))

    # add arkui-x to PATH
    os.environ['PATH'] = f'{cwd}/.arkui-x/android:{os.environ.get("PATH")}'

    # generate unsigned_hap_path_list and run ohpm install
    make_env(options.build_profile, cwd, options.ohpm_registry)

    # invoke hvigor to build hap or app
    hvigor_build(cwd, options)

    # generate a json file to record the path of all unsigned haps, and When signing hap later, 
    # this json file will serve as input to provide path information for each unsigned hap.
    gen_unsigned_hap_path_json(options.build_profile, cwd, options)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
