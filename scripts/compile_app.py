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
    parser.add_argument('--hvigor-home', help='hvigor home')
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
    parser.add_argument('--build-modules', help='build modules', nargs='+', default=[])
    parser.add_argument('--use-hvigor-cache', help='use hvigor cache', action='store_true')
    parser.add_argument('--hvigor-obfuscation', help='hvigor obfuscation', action='store_true')
    parser.add_argument('--target-out-dir', help='base output dir')
    parser.add_argument('--target-app-dir', help='target output dir')

    options = parser.parse_args(args)
    return options


def make_env(build_profile: str, cwd: str, ohpm_registry: str, options):
    '''
    Set up the application compilation environment and run "ohpm install"
    :param build_profile: module compilation information file
    :param cwd: app project directory
    :param ohpm_registry: ohpm registry
    :return: None
    '''
    print(f"build_profile:{build_profile}; cwd:{cwd}")
    cur_dir = os.getcwd()
    root_dir = os.path.dirname(os.path.dirname(cur_dir))
    ohpm_path = os.path.join(root_dir, "prebuilts/build-tools/common/oh-command-line-tools/ohpm/bin/ohpm")
    if not os.path.exists(ohpm_path):
        ohpm_path = "ohpm"
    with open(build_profile, 'r') as input_f:
        build_info = json5.load(input_f)
        modules_list = build_info.get('modules')
        ohpm_install_cmd = [ohpm_path, 'install']
        if ohpm_registry:
            ohpm_install_cmd.append('--registry=' + ohpm_registry)
        env = {
            'PATH': f"{os.path.dirname(os.path.abspath(options.nodejs))}:{os.environ.get('PATH')}",
            'NODE_HOME': os.path.dirname(os.path.abspath(options.nodejs)),
        }
        os.chdir(cwd)
        if os.path.exists(os.path.join(cwd, 'hvigorw')):
            subprocess.run(['chmod', '+x', 'hvigorw'])
        if os.path.exists(os.path.join(cwd, '.arkui-x/android/gradlew')):
            subprocess.run(['chmod', '+x', '.arkui-x/android/gradlew'])
        proc = subprocess.Popen(ohpm_install_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=env,
                                encoding='utf-8')
        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise Exception('ReturnCode:{}. ohpm install failed. {}'.format(
                proc.returncode, stdout))
    os.chdir(cur_dir)


def get_integrated_project_config(cwd: str):
    print(f"[0/0] project dir: {cwd}")
    with open(os.path.join(cwd, 'hvigor/hvigor-config.json5'), 'r') as input_f:
        hvigor_info = json5.load(input_f)
        model_version = hvigor_info.get('modelVersion')
    return model_version


def get_hvigor_version(cwd: str):
    print(f"[0/0] project dir: {cwd}")
    with open(os.path.join(cwd, 'hvigor/hvigor-config.json5'), 'r') as input_f:
        hvigor_info = json5.load(input_f)
        hvigor_version = hvigor_info.get('hvigorVersion')
    return hvigor_version


def get_unsigned_hap_path(project_name: str, src_path: str, cwd: str, options):
    hvigor_version = get_hvigor_version(cwd)
    model_version = get_integrated_project_config(cwd)
    if options.test_hap:
        if options.target_app_dir and ((hvigor_version and float(hvigor_version[:3]) > 4.1) or model_version):
            new_src_path = os.path.join(options.target_out_dir, options.target_app_dir, project_name, src_path)
            unsigned_hap_path = os.path.join(
                new_src_path, 'build/default/outputs/ohosTest')
        else:
            unsigned_hap_path = os.path.join(
                cwd, src_path, 'build/default/outputs/ohosTest')
    else:
        if options.target_app_dir and ((hvigor_version and float(hvigor_version[:3]) > 4.1) or model_version):
            new_src_path = os.path.join(options.target_out_dir, options.target_app_dir, project_name, src_path)
            unsigned_hap_path = os.path.join(
                new_src_path, 'build/default/outputs/default')
        else:
            unsigned_hap_path = os.path.join(
                cwd, src_path, 'build/default/outputs/default')
    return unsigned_hap_path


def gen_unsigned_hap_path_json(build_profile: str, cwd: str, options):
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
            project_name = options.build_profile.replace("/build-profile.json5", "").split("/")[-1]
            unsigned_hap_path = get_unsigned_hap_path(project_name, src_path, cwd, options)
            hap_file = build_utils.find_in_directory(
                unsigned_hap_path, '*-unsigned.hap')
            hsp_file = build_utils.find_in_directory(
                unsigned_hap_path, '*-unsigned.hsp')
            unsigned_hap_path_list.extend(hap_file)
            unsigned_hap_path_list.extend(hsp_file)
        unsigned_hap_path_json['unsigned_hap_path_list'] = unsigned_hap_path_list
    file_utils.write_json_file(options.output_file, unsigned_hap_path_json)


def copy_libs(cwd: str, system_lib_module_info_list: list, ohos_app_abi: str, module_libs_dir: str):
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


def hvigor_write_log(cmd, cwd, env):
    proc = subprocess.Popen(cmd, 
                            cwd=cwd, 
                            env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='utf-8')
    stdout, stderr = proc.communicate()
    for line in stdout.splitlines():
        print(f"[1/1] Hvigor info: {line}")
    for line in stderr.splitlines():
        print(f"[2/2] Hvigor warning: {line}")
    os.makedirs(os.path.join(cwd, 'build'), exist_ok=True)
    with open(os.path.join(cwd, 'build', 'build.log'), 'w') as f:
        f.write(f'{stdout}\n')
        f.write(f'{stderr}\n')
    if proc.returncode or "ERROR: BUILD FAILED" in stderr or "ERROR: BUILD FAILED" in stdout:
        raise Exception('ReturnCode:{}. Hvigor build failed: {}'.format(proc.returncode, stderr))
    print("[0/0] Hvigor build end")


def build_hvigor_cmd(cwd: str, model_version: str, options):
    cmd = ['bash']
    hvigor_version = get_hvigor_version(cwd)
    if hvigor_version:
        if options.hvigor_home:
            cmd.extend([f'{os.path.abspath(options.hvigor_home)}/hvigorw'])
        else:
            cmd.extend(['hvigorw'])
    elif model_version:
        code_home = os.path.dirname(os.path.dirname(options.sdk_home))
        hvigor_home = f"{code_home}/tool/command-line-tools/bin"
        cmd.extend([f'{hvigor_home}/hvigorw'])
    else:
        cmd.extend(['./hvigorw'])
    
    if options.test_hap:
        cmd.extend(['--mode', 'module', '-p',
               f'module={options.test_module}@ohosTest', 'assembleHap'])
    elif options.build_modules:
        cmd.extend(['assembleHap', '--mode',
               'module', '-p', 'product=default', '-p', 'module=' + ','.join(options.build_modules)])
    else:
        cmd.extend(['--mode',
               options.build_level, '-p', 'product=default', options.assemble_type])

    if options.enable_debug:
        cmd.extend(['-p', 'debuggable=true'])
    else:
        cmd.extend(['-p', 'debuggable=false'])

    if options.use_hvigor_cache and os.environ.get('CACHE_BASE'):
        hvigor_cache_dir = os.path.join(os.environ.get('CACHE_BASE'), 'hvigor_cache')
        os.makedirs(hvigor_cache_dir, exist_ok=True)
        cmd.extend(['-p', f'build-cache-dir={hvigor_cache_dir}'])

    if options.hvigor_obfuscation:
        cmd.extend(['-p', 'buildMode=release'])
    else:
        cmd.extend(['-p', 'hvigor-obfuscation=false'])
    
    if options.target_app_dir and options.target_app_dir != "":
        if (hvigor_version and float(hvigor_version[:3]) > 4.1) or model_version:
            target_out_dir = os.path.abspath(options.target_out_dir)
            output_dir = os.path.join(target_out_dir, options.target_app_dir)
            cmd.extend(['-c', f'properties.ohos.buildDir="{output_dir}"'])
        
    cmd.extend(['--no-daemon'])
    
    print("[0/0] hvigor cmd: " + ' '.join(cmd))
    return cmd


def set_sdk_path(cwd: str, model_version: str, options, env):
    if 'sdk.dir' not in options.sdk_type_name and model_version:
        write_env_sdk(options, env)
    else:
        write_local_properties(cwd, options)


def write_local_properties(cwd: str, options):
    sdk_dir = options.sdk_home
    nodejs_dir = os.path.abspath(
        os.path.dirname(os.path.dirname(options.nodejs)))
    with open(os.path.join(cwd, 'local.properties'), 'w') as f:
        for sdk_type in options.sdk_type_name:
            f.write(f'{sdk_type}={sdk_dir}\n')
        f.write(f'nodejs.dir={nodejs_dir}\n')


def write_env_sdk(options, env):
    sdk_dir = options.sdk_home
    env['DEVECO_SDK_HOME'] = sdk_dir


def hvigor_sync(cwd: str, model_version: str, env):
    if not model_version:
        subprocess.run(['bash', './hvigorw', '--sync', '--no-daemon'],
                   cwd=cwd,
                   env=env,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def hvigor_build(cwd: str, options):
    '''
    Run hvigorw to build the app or hap
    :param cwd: app project directory
    :param options: command line parameters
    :return: None
    '''
    model_version = get_integrated_project_config(cwd)
    print(f"[0/0] model_version: {model_version}")

    cmd = build_hvigor_cmd(cwd, model_version, options)

    print("[0/0] Hvigor clean start")
    env = os.environ.copy()
    env['CI'] = 'true'

    set_sdk_path(cwd, model_version, options, env)

    hvigor_sync(cwd, model_version, env)
    
    print("[0/0] Hvigor build start")
    hvigor_write_log(cmd, cwd, env)


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
    make_env(options.build_profile, cwd, options.ohpm_registry, options)

    # invoke hvigor to build hap or app
    hvigor_build(cwd, options)

    # generate a json file to record the path of all unsigned haps, and When signing hap later, 
    # this json file will serve as input to provide path information for each unsigned hap.
    gen_unsigned_hap_path_json(options.build_profile, cwd, options)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
