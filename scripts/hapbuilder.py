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
import subprocess
import sys
import shutil
import os
import tempfile
import json
from util import build_utils  # noqa: E402


def sign_hap(options, unsigned_hap_path: str, signed_hap_path: str):
    cmd = ['python3', options.sign_hap_py_path]
    cmd.extend(['--hapsigner', options.hapsigner])
    cmd.extend(['--sign-algo', options.sign_algo])
    cmd.extend(['--keyalias', options.keyalias])
    cmd.extend(['--inFile', unsigned_hap_path])
    cmd.extend(['--outFile', signed_hap_path])
    cmd.extend(['--profileFile', options.certificate_profile])
    cmd.extend(['--keystoreFile', options.keystore_path])
    cmd.extend(['--keystorePwd', options.keystorepasswd])
    cmd.extend(['--keyPwd', options.private_key_path])
    cmd.extend(['--certificate-file', options.certificate_file])
    cmd.extend(['--profileSigned', '1'])
    cmd.extend(['--inForm', 'zip'])
    cmd.extend(['--compatible_version', options.sign_compatible_version])
    child = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    stdout, stderr = child.communicate()
    if child.returncode:
        print(stdout.decode(), stderr.decode())
        raise Exception("Failed to sign hap {}.".format(options.sign_hap_py_path))


def add_resources(packaged_resources: list, package_dir: str, packing_cmd: list):
    if packaged_resources:
        build_utils.extract_all(packaged_resources,
                                package_dir,
                                no_clobber=False)
        index_file_path = os.path.join(package_dir, 'resources.index')
        if os.path.exists(index_file_path):
            packing_cmd.extend(['--index-path', index_file_path])
            resources_path = os.path.join(package_dir, 'resources')
            if os.path.exists(resources_path):
                packing_cmd.extend(['--resources-path', resources_path])


def add_assets(options, package_dir: str, packing_cmd: list):
    packaged_js_assets, assets = options.packaged_js_assets, options.assets
    if options.app_profile:
        assets_dir = os.path.join(package_dir, 'ets')
        js_assets_dir = os.path.join(package_dir, 'js')
    else:
        assets_dir = os.path.join(package_dir, 'assets')

    if packaged_js_assets:
        build_utils.extract_all(packaged_js_assets,
                                package_dir,
                                no_clobber=False)
    if options.build_mode == "release":
        for root, _, files in os.walk(assets_dir):
            for f in files:
                filename = os.path.join(root, f)
                if filename.endswith('.js.map'):
                    os.unlink(filename)
    if assets:
        if not os.path.exists(assets_dir):
            os.mkdir(assets_dir)
        for item in assets:
            if os.path.isfile(item):
                shutil.copyfile(
                    item, os.path.join(assets_dir, os.path.basename(item)))
            elif os.path.isdir(item):
                shutil.copytree(
                    item, os.path.join(assets_dir, os.path.basename(item)))
    if os.path.exists(assets_dir) and len(os.listdir(assets_dir)) != 0:
        if options.app_profile:
            packing_cmd.extend(['--ets-path', assets_dir])
        else:
            packing_cmd.extend(['--assets-path', assets_dir])
    if options.app_profile:
        if os.path.exists(js_assets_dir) and len(os.listdir(js_assets_dir)) != 0:
            packing_cmd.extend(['--js-path', js_assets_dir])


def get_ark_toolchain_version(options):
    cmd = [options.nodejs_path, options.js2abc_js, '--bc-version']
    return build_utils.check_output(cmd).strip('\n')


def tweak_hap_profile(options, package_dir: str):
    config_name = 'config.json'
    if options.app_profile:
        config_name = 'module.json'
    hap_profile = os.path.join(package_dir, config_name)
    if not os.path.exists(hap_profile):
        raise Exception('Error: {} of hap file not exists'.format(config_name))
    config = {}
    with open(hap_profile, 'r') as fileobj:
        config = json.load(fileobj)
        if options.app_profile:
            config.get('module')['virtualMachine'] = 'ark{}'.format(
                get_ark_toolchain_version(options))
        else:
            config.get('module').get('distro')['virtualMachine'] = 'ark{}'.format(
                get_ark_toolchain_version(options))
    build_utils.write_json(config, hap_profile)


def create_hap(options, signed_hap: str):
    with build_utils.temp_dir() as package_dir, tempfile.NamedTemporaryFile(
            suffix='.hap') as output:
        packing_cmd = ['java', '-jar', options.hap_packing_tool]
        packing_cmd.extend(
            ['--mode', 'hap', '--force', 'true', '--out-path', output.name])

        hap_profile_path = os.path.join(package_dir,
                                        os.path.basename(options.hap_profile))
        shutil.copy(options.hap_profile, hap_profile_path)
        packing_cmd.extend(['--json-path', hap_profile_path])
        add_assets(options, package_dir, packing_cmd)

        add_resources(options.packaged_resources, package_dir, packing_cmd)
        if options.enable_ark:
            tweak_hap_profile(options, package_dir)
        if options.dso:
            lib_path = os.path.join(package_dir, "lib")
            hap_lib_path = os.path.join(lib_path, options.ohos_app_abi)
            os.makedirs(hap_lib_path, exist_ok=True)
            for dso in sorted(options.dso):
                shutil.copy(dso, hap_lib_path)
            packing_cmd.extend(['--lib-path', lib_path])

        build_utils.check_output(packing_cmd)

        sign_hap(options, output.name, signed_hap)


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--hap-path', help='path to output hap')
    parser.add_option('--hapsigner', help='path to signer')
    parser.add_option('--assets', help='path to assets')
    parser.add_option('--dso',
                      action="append",
                      help='path to dynamic shared objects')
    parser.add_option('--ohos-app-abi', help='ohos app abi')
    parser.add_option('--hap-profile', help='path to hap profile')
    parser.add_option('--nodejs-path', help='path to node')
    parser.add_option('--js2abc-js', help='path to ts2abc.js')
    parser.add_option('--enable-ark',
                      action='store_true',
                      default=False,
                      help='whether to transform js to ark bytecode')
    parser.add_option('--hap-packing-tool', help='path to hap packing tool')
    parser.add_option('--private-key-path', help='path to private key')
    parser.add_option('--sign-algo', help='signature algorithm')
    parser.add_option('--certificate-profile',
                      help='path to certificate profile')
    parser.add_option('--keyalias', help='keyalias')
    parser.add_option('--keystore-path', help='path to keystore')
    parser.add_option('--keystorepasswd', help='password of keystore')
    parser.add_option('--certificate-file', help='path to certificate file')
    parser.add_option('--packaged-resources',
                      help='path to packaged resources')
    parser.add_option('--packaged-js-assets',
                      help='path to packaged js assets')
    parser.add_option('--app-profile', default=False,
                      help='path to packaged js assets')
    parser.add_option('--build-mode', help='debug mode or release mode')
    
    parser.add_option('--sign_hap_py_path', help='sign_hap_py_path')
    parser.add_option('--sign_compatible_version', default='', help='limit compatible_Version')

    options, _ = parser.parse_args(args)
    if options.assets:
        options.assets = build_utils.parse_gn_list(options.assets)
    return options


def main(args):
    options = parse_args(args)

    inputs = [
        options.hap_profile, options.packaged_js_assets,
        options.packaged_resources, options.certificate_file,
        options.keystore_path, options.certificate_profile
    ]
    depfiles = []
    for dire in options.assets:
        depfiles += (build_utils.get_all_files(dire))
    if options.dso:
        depfiles.extend(options.dso)

    build_utils.call_and_write_depfile_if_stale(
        lambda: create_hap(options, options.hap_path),
        options,
        depfile_deps=depfiles,
        input_paths=inputs + depfiles,
        input_strings=[
            options.keystorepasswd, options.keyalias, options.sign_algo,
            options.private_key_path
        ],
        output_paths=([options.hap_path]),
        force=False,
        add_pydeps=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
