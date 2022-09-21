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
    parser.add_option('--ark-ts2abc-dir', help='path to ark ts2abc dir')
    parser.add_option('--ark-es2abc-dir', help='path to ark es2abc dir')
    parser.add_option('--ace-loader-home', help='path to ace-loader dir.')
    parser.add_option('--ets-loader-home', help='path to ets-loader dir.')
    parser.add_option('--app-profile', default=False, help='path to app-profile.')
    parser.add_option('--manifest-file-path', help='path to manifest.json dir.')

    options, _ = parser.parse_args(args)
    options.js_assets_dir = build_utils.parse_gn_list(options.js_assets_dir)
    options.ets_assets_dir = build_utils.parse_gn_list(options.ets_assets_dir)
    return options

def make_my_env(build_dir, options, js2abc, ability_index):
    out_dir = os.path.abspath(os.path.dirname(options.output))
    assets_dir = os.path.join(out_dir, "assets")
    if options.app_profile:
        if js2abc:
            assets_dir = os.path.join(assets_dir, "js")
        else:
            assets_dir = os.path.join(assets_dir, "ets")
    gen_dir = os.path.join(out_dir, "gen")
    my_env = {
        "aceModuleBuild": assets_dir,
        "buildMode": options.build_mode,
        "PATH": os.environ.get('PATH'),
        "appResource": os.path.join(gen_dir, "ResourceTable.txt")
    }
    with open(options.hap_profile) as profile:
        config = json.load(profile)
        ability_cnt = len(config['module']['abilities'])
        if ability_index < ability_cnt and (options.js_asset_cnt > 1 or options.ets_asset_cnt > 1):
            if config['module']['abilities'][ability_index].__contains__('forms'):
                my_env["abilityType"] = 'form'
            else:
                my_env["abilityType"] = config['module']['abilities'][ability_index]['type']
        elif config['module'].__contains__('testRunner'):
            my_env["abilityType"] = 'testrunner'

    if options.app_profile:
        my_env["aceProfilePath"] = os.path.join(gen_dir, "resources/base/profile")
        my_env["aceModuleJsonPath"] = os.path.abspath(options.hap_profile)
    else:
        manifest = os.path.join(build_dir, 'manifest.json')
        my_env["aceManifestPath"] = manifest
    return my_env

def make_manifest_data(config, options, js2abc, ability_index):
    data = dict()
    data['appID'] = config['app']['bundleName']
    ability_cnt = len(config['module']['abilities'])
    if ability_index < ability_cnt and config['module']['abilities'][ability_index].__contains__("label"):
        data['appName'] = config['module']['abilities'][ability_index]['label']
    if options.app_profile:
        data['versionName'] = config['app']['versionName']
        data['versionCode'] = config['app']['versionCode']
        data['pages'] = config['module']['pages']
        data['deviceType'] = config['module']['deviceTypes']
    else:
        data['versionName'] = config['app']['version']['name']
        data['versionCode'] = config['app']['version']['code']
        if ability_index < len(config['module']['js']):
            data['pages'] = config['module']['js'][ability_index]['pages']
            data['window'] = config['module']['js'][ability_index]['window']
            if config['module']['js'][ability_index].get('type') == 'form':
                data['pages']  = []
                data['type']  = 'form'
        data['deviceType'] = config['module']['deviceType']
    if js2abc and (config['module']['abilities'][0].get('srcLanguage') == 'ets' or ability_index >= ability_cnt):
        for js_page in config['module']['js']:
            if js_page.get('type') == 'form':
                data['pages'] = js_page.get('pages')
                data['type'] = js_page.get('type')
                data['window'] = js_page.get('window')
    if not js2abc:
        if not options.app_profile and ability_index < len(config['module']['js']):
            data['mode'] = config['module']['js'][ability_index].get('mode')
    return data

def build_ace(cmd, options, js2abc, loader_home, assets_dir):
    gen_dir = ''
    src_path = ''
    if js2abc:
        for asset_index in range(options.js_asset_cnt):
            ability_dir = os.path.relpath(assets_dir[asset_index], loader_home)
            if options.js_sources_file:
                with open(options.js_sources_file, 'wb') as js_sources_file:
                    sources = get_all_js_sources(ability_dir)
                    js_sources_file.write('\n'.join(sources).encode())
            build_dir = os.path.abspath(os.path.join(options.manifest_file_path, 'js', str(asset_index)))
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            my_env = make_my_env(build_dir, options, js2abc, asset_index)
            my_env["aceModuleRoot"] = ability_dir
            gen_dir = my_env.get("aceModuleBuild")
            if options.app_profile:
                gen_dir = os.path.dirname(gen_dir)
            my_env.update({"cachePath": os.path.join(build_dir, ".cache")})
            if not options.app_profile:
                src_path = 'default'
            manifest = os.path.join(build_dir, 'manifest.json')
            if not os.path.exists(manifest):
                with open(options.hap_profile) as profile:
                    config = json.load(profile)
                    data = make_manifest_data(config, options, js2abc, asset_index)
                    build_utils.write_json(data, manifest)
            if not options.app_profile:
                with open(options.hap_profile) as profile:
                    config = json.load(profile)
                    if config['module'].__contains__('testRunner'):
                        src_path = config['module']['testRunner']['srcPath']
                    if options.js_asset_cnt > 1 and asset_index < len(config['module']['abilities']):
                        if 'srcPath' in config['module']['abilities'][asset_index]:
                            src_path = config['module']['abilities'][asset_index]['srcPath']
                    if config['module']['abilities'][0].get('srcLanguage') == 'ets':
                        for ability in config['module']['abilities']:
                            if ability.__contains__('forms'):
                                src_path = ability['forms'][0].get('name')
                    if asset_index >= len(config['module']['abilities']):
                        for ability in config['module']['abilities']:
                            if ability.__contains__('forms'):
                                src_path = ability['forms'][0].get('name')

                    my_env["aceModuleBuild"] = os.path.join(my_env.get("aceModuleBuild"), src_path)
            build_utils.check_output(
                cmd, cwd=loader_home, env=my_env)
    else:
        for asset_index in range(options.ets_asset_cnt):
            ability_dir = os.path.relpath(assets_dir[asset_index], loader_home)
            if options.js_sources_file:
                with open(options.js_sources_file, 'wb') as js_sources_file:
                    sources = get_all_js_sources(ability_dir)
                    js_sources_file.write('\n'.join(sources).encode())
            build_dir = os.path.abspath(os.path.join(options.manifest_file_path, 'ets', str(asset_index)))
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            my_env = make_my_env(build_dir, options, js2abc, asset_index)
            my_env["aceModuleRoot"] = ability_dir
            gen_dir = my_env.get("aceModuleBuild")
            if options.app_profile:
                gen_dir = os.path.dirname(gen_dir)
            if not options.app_profile:
                src_path = 'default'
            manifest = os.path.join(build_dir, 'manifest.json')
            if not os.path.exists(manifest):
                with open(options.hap_profile) as profile:
                    config = json.load(profile)
                    data = make_manifest_data(config, options, js2abc, asset_index)
                    build_utils.write_json(data, manifest)
            if not options.app_profile:
                with open(options.hap_profile) as profile:
                    config = json.load(profile)
                    if 'srcPath' in config['module']['abilities'][asset_index]:
                        src_path = config['module']['abilities'][asset_index]['srcPath']
                    my_env["aceModuleBuild"] = os.path.join(my_env.get("aceModuleBuild"), src_path)
            build_utils.check_output(
                cmd, cwd=loader_home, env=my_env)
    if options.app_profile:
        build_utils.zip_dir(options.output,
                            gen_dir,
                            zip_prefix_path=src_path)
    elif not options.app_profile and not options.hap_profile:
        build_utils.zip_dir(options.output,
                            gen_dir,
                            zip_prefix_path='assets/js/{}/'.format(src_path))
    else:
        build_utils.zip_dir(options.output,
                            gen_dir,
                            zip_prefix_path='assets/js/')


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
    options.js_asset_cnt = 0
    options.ets_asset_cnt = 0
    if options.js_assets_dir:
        options.js_asset_cnt = len(options.js_assets_dir)
        for asset_index in range(options.js_asset_cnt):
            depfiles.extend(build_utils.get_all_files(options.js_assets_dir[asset_index]))
    if options.ets_assets_dir:
        options.ets_asset_cnt = len(options.ets_assets_dir)
        for asset_index in range(options.ets_asset_cnt):
            depfiles.extend(build_utils.get_all_files(options.ets_assets_dir[asset_index]))
    if not options.js_assets_dir and not options.ets_assets_dir:
        with ZipFile(options.output, 'w') as file:
            return

    if options.ark_ts2abc_dir:
        depfiles.extend(build_utils.get_all_files(options.ark_ts2abc_dir))

    if options.ark_es2abc_dir:
        depfiles.extend(build_utils.get_all_files(options.ark_es2abc_dir))

    depfiles.append(options.webpack_js)
    depfiles.append(options.webpack_config_js)
    depfiles.append(options.webpack_config_ets)
    depfiles.extend(build_utils.get_all_files(options.ace_loader_home))
    depfiles.extend(build_utils.get_all_files(options.ets_loader_home))

    node_js = os.path.relpath(options.nodejs_path, options.ace_loader_home)

    if options.js_assets_dir:
        js2abc = True
        loader_home = options.ace_loader_home
        assets_dir = options.js_assets_dir
        cmd = [
            node_js,
            os.path.relpath(
                options.webpack_js, options.ace_loader_home),
            '--config',
            os.path.relpath(
                options.webpack_config_js, options.ace_loader_home)
        ]
        ark_ts2abc_dir = os.path.relpath(
            options.ark_ts2abc_dir, options.ace_loader_home)
        if options.app_profile:
            cmd.extend(['--env', 'buildMode={}'.format(options.build_mode), 'compilerType=ark',
                        'arkFrontendDir={}'.format(ark_ts2abc_dir), 'nodeJs={}'.format(node_js)])
        else:
            cmd.extend(['--env', 'compilerType=ark',
                    'arkFrontendDir={}'.format(ark_ts2abc_dir), 'nodeJs={}'.format(node_js)])
        build_utils.call_and_write_depfile_if_stale(
            lambda: build_ace(cmd, options, js2abc, loader_home, assets_dir),
            options,
            depfile_deps=depfiles,
            input_paths=depfiles + inputs,
            input_strings=cmd + [options.build_mode],
            output_paths=([options.output]),
            force=False,
            add_pydeps=False)

    if options.ets_assets_dir:
        js2abc = False
        loader_home = options.ets_loader_home
        assets_dir = options.ets_assets_dir
        cmd = [
            node_js,
            os.path.relpath(
                options.webpack_js, options.ets_loader_home),
            '--config',
            os.path.relpath(
                options.webpack_config_ets, options.ets_loader_home)
        ]
        ark_es2abc_dir = os.path.relpath(
            options.ark_es2abc_dir, options.ets_loader_home)
        if options.app_profile:
            cmd.extend(['--env', 'buildMode={}'.format(options.build_mode), 'compilerType=ark',
                        'arkFrontendDir={}'.format(ark_es2abc_dir), 'nodeJs={}'.format(node_js)])
        else:
            cmd.extend(['--env', 'compilerType=ark',
                        'arkFrontendDir={}'.format(ark_es2abc_dir), 'nodeJs={}'.format(node_js)])
        build_utils.call_and_write_depfile_if_stale(
            lambda: build_ace(cmd, options, js2abc, loader_home, assets_dir),
            options,
            depfile_deps=depfiles,
            input_paths=depfiles + inputs,
            input_strings=cmd + [options.build_mode],
            output_paths=([options.output]),
            force=False,
            add_pydeps=False)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
