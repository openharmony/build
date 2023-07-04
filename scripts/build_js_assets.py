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
import json

from zipfile import ZipFile  # noqa: E402
from util import build_utils  # noqa: E402


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--output', help='stamp file')
    parser.add_option('--js-assets-dir', help='js assets directory')
    parser.add_option('--ets-assets-dir', help='ets assets directory')
    parser.add_option('--js-forms-dir', help='js forms directory')
    parser.add_option('--testrunner-dir', help='testrunner directory')
    parser.add_option('--nodejs-path', help='path to nodejs app')
    parser.add_option('--webpack-js', help='path to webpack.js')
    parser.add_option('--webpack-config-js', help='path to webpack.config.js')
    parser.add_option('--webpack-config-ets', help='path to webpack.rich.config.js')
    parser.add_option('--hap-profile', help='path to hap profile')
    parser.add_option('--build-mode', help='debug mode or release mode')
    parser.add_option('--js-sources-file', help='path to js sources file')
    parser.add_option('--js2abc',
                      action='store_true',
                      default=False,
                      help='whether to transform js to ark bytecode')
    parser.add_option('--ets2abc',
                      action='store_true',
                      default=False,
                      help='whether to transform ets to ark bytecode')
    parser.add_option('--ark-es2abc-dir', help='path to ark es2abc dir')
    parser.add_option('--ace-loader-home', help='path to ace-loader dir.')
    parser.add_option('--ets-loader-home', help='path to ets-loader dir.')
    parser.add_option('--app-profile', default=False, help='path to app-profile.')
    parser.add_option('--manifest-file-path', help='path to manifest.json dir.')

    options, _ = parser.parse_args(args)
    options.js_assets_dir = build_utils.parse_gn_list(options.js_assets_dir)
    options.ets_assets_dir = build_utils.parse_gn_list(options.ets_assets_dir)
    options.js_forms_dir = build_utils.parse_gn_list(options.js_forms_dir)
    options.testrunner_dir = build_utils.parse_gn_list(options.testrunner_dir)
    return options


def make_my_env(options, js2abc):
    out_dir = os.path.abspath(os.path.dirname(options.output))
    gen_dir = os.path.join(out_dir, "gen")
    assets_dir = os.path.join(out_dir, "assets")
    if options.app_profile:
        if js2abc:
            assets_dir = os.path.join(assets_dir, "js")
        else:
            assets_dir = os.path.join(assets_dir, "ets")
    my_env = {
        "aceModuleBuild": assets_dir,
        "buildMode": options.build_mode,
        "PATH": os.environ.get('PATH'),
        "appResource": os.path.join(gen_dir, "ResourceTable.txt")
    }
    if options.app_profile:
        my_env["aceProfilePath"] = os.path.join(gen_dir, "resources/base/profile")
        my_env["aceModuleJsonPath"] = os.path.abspath(options.hap_profile)
    return my_env


def make_manifest_data(config, options, js2abc, asset_index, assets_cnt, src_path):
    data = dict()
    data['appID'] = config['app']['bundleName']
    if options.app_profile:
        data['versionName'] = config['app']['versionName']
        data['versionCode'] = config['app']['versionCode']
        data['pages'] = config['module']['pages']
        data['deviceType'] = config['module']['deviceTypes']
    else:
        data['appName'] = config['module']['abilities'][asset_index].get('label')
        data['versionName'] = config['app']['version']['name']
        data['versionCode'] = config['app']['version']['code']
        data['deviceType'] = config['module']['deviceType']
        for js_module in config['module']['js']:
            js_module_name = js_module.get('name').split('.')[-1]

            # According to the page name and ability entry match the corresponding page for ability
            # Compatibility with mismatches due to "MainAbility" and "default"
            if js_module_name == src_path or (js_module_name == 'MainAbility' and src_path == 'default') \
               or (js_module_name == 'default' and src_path == 'MainAbility'):
                data['pages'] = js_module.get('pages')
                data['window'] = js_module.get('window')
                if js_module.get('type') == 'form' and options.js_forms_dir:
                    data['type'] = 'form'
            if not js2abc:
                data['mode'] = js_module.get('mode')
    return data


def build_ace(cmd, options, js2abc, loader_home, assets_dir, assets_name):
    my_env = make_my_env(options, js2abc)
    gen_dir = my_env.get("aceModuleBuild")
    assets_cnt = len(assets_dir)
    for asset_index in range(assets_cnt):
        ability_dir = os.path.relpath(assets_dir[asset_index], loader_home)
        my_env["aceModuleRoot"] = ability_dir
        if options.js_sources_file:
            with open(options.js_sources_file, 'wb') as js_sources_file:
                sources = get_all_js_sources(ability_dir)
                js_sources_file.write('\n'.join(sources).encode())
        src_path = os.path.basename(assets_dir[asset_index])

        # Create a fixed directory for manifest.json
        if js2abc:
            build_dir = os.path.abspath(os.path.join(options.manifest_file_path, 'js', src_path))
            my_env.update({"cachePath": os.path.join(build_dir, ".cache")})
        else:
            build_dir = os.path.abspath(os.path.join(options.manifest_file_path, 'ets', src_path))
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        manifest = os.path.join(build_dir, 'manifest.json')

        # Determine abilityType according to config.json
        if assets_name == 'testrunner_dir':
            my_env["abilityType"] = 'testrunner'
        elif assets_name != 'js_forms_dir' and not options.app_profile and assets_cnt > 1:
            with open(options.hap_profile) as profile:
                config = json.load(profile)
                if config['module']['abilities'][asset_index].__contains__('forms'):
                    my_env["abilityType"] = 'form'
                else:
                    my_env["abilityType"] = config['module']['abilities'][asset_index]['type']
        else:
            my_env["abilityType"] = 'page'

        # Generate manifest.json only when abilityType is page
        data = dict()
        if my_env["abilityType"] == 'page':
            with open(options.hap_profile) as profile:
                config = json.load(profile)
                data = make_manifest_data(config, options, js2abc, asset_index, assets_cnt, src_path)
                build_utils.write_json(data, manifest)

            # If missing page, skip it
            if not data.__contains__('pages'):
                print('Warning: There is no page matching this {}'.format(src_path))
                continue

        if not options.app_profile:
            my_env["aceManifestPath"] = manifest
            my_env["aceModuleBuild"] = os.path.join(gen_dir, src_path)
        build_utils.check_output(cmd, cwd=loader_home, env=my_env)

    if options.app_profile:
        gen_dir = os.path.dirname(gen_dir)
        build_utils.zip_dir(options.output, gen_dir)
    else:
        build_utils.zip_dir(options.output, gen_dir, zip_prefix_path='assets/js/')


def get_all_js_sources(base):
    sources = []
    for root, _, files in os.walk(base):
        for file in files:
            if file[-3:] in ('.js', '.ts'):
                sources.append(os.path.join(root, file))

    return sources


def main(args):
    options = parse_args(args)

    inputs = [
        options.nodejs_path, options.webpack_js, options.webpack_config_js, options.webpack_config_ets
    ]
    depfiles = []
    if not options.js_assets_dir and not options.ets_assets_dir:
        with ZipFile(options.output, 'w') as file:
            return

    if options.ark_es2abc_dir:
        depfiles.extend(build_utils.get_all_files(options.ark_es2abc_dir))

    depfiles.append(options.webpack_js)
    depfiles.append(options.webpack_config_js)
    depfiles.append(options.webpack_config_ets)
    depfiles.extend(build_utils.get_all_files(options.ace_loader_home))
    depfiles.extend(build_utils.get_all_files(options.ets_loader_home))

    node_js = os.path.relpath(options.nodejs_path, options.ace_loader_home)
    assets_dict = dict()
    if options.js_assets_dir:
        assets_dict['js_assets_dir'] = options.js_assets_dir
    if options.ets_assets_dir:
        assets_dict['ets_assets_dir'] = options.ets_assets_dir
    if options.js_forms_dir:
        assets_dict['js_forms_dir'] = options.js_forms_dir
    if options.testrunner_dir:
        assets_dict['testrunner_dir'] = options.testrunner_dir

    for assets_name, assets_dir in assets_dict.items():
        for asset in assets_dir:
            depfiles.extend(build_utils.get_all_files(asset))
        if assets_name == 'ets_assets_dir':
            js2abc = False
            loader_home = options.ets_loader_home
            webpack_config = options.webpack_config_ets
        else:
            js2abc = True
            loader_home = options.ace_loader_home
            webpack_config = options.webpack_config_js
        cmd = [
            node_js,
            os.path.relpath(options.webpack_js, loader_home),
            '--config',
            os.path.relpath(webpack_config, loader_home)
        ]
        ark_es2abc_dir = os.path.relpath(options.ark_es2abc_dir, loader_home)
        if options.app_profile:
            cmd.extend(['--env', 'buildMode={}'.format(options.build_mode), 'compilerType=ark',
                        'arkFrontendDir={}'.format(ark_es2abc_dir), 'nodeJs={}'.format(node_js)])
        else:
            cmd.extend(['--env', 'compilerType=ark',
                        'arkFrontendDir={}'.format(ark_es2abc_dir), 'nodeJs={}'.format(node_js)])
        build_utils.call_and_write_depfile_if_stale(
            lambda: build_ace(cmd, options, js2abc, loader_home, assets_dir, assets_name),
            options,
            depfile_deps=depfiles,
            input_paths=depfiles + inputs,
            input_strings=cmd + [options.build_mode],
            output_paths=([options.output]),
            force=False,
            add_pydeps=False)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
