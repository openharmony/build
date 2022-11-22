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

import sys
import argparse
import os
import json
import copy

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util import build_utils  # noqa E402

deps_metadta_cache = {}


def get_all_deps(direct_deps):
    if direct_deps == []:
        return []
    deps = copy.deepcopy(direct_deps)
    all_deps = set()
    all_deps.update(deps)
    while len(deps) > 0:
        dep = deps.pop(0)
        if dep not in deps_metadta_cache:
            with open(dep) as dep_fp:
                deps_metadta_cache[dep] = json.load(dep_fp).get('root')
        for n in deps_metadta_cache[dep].get('metadata_deps'):
            if n not in all_deps:
                deps.append(n)
                all_deps.add(n)
    return sorted(list(all_deps))


def get_deps_metadata(deps):
    return [deps_metadta_cache[d] for d in deps]


def get_deps_of_type(deps_data, target_type):
    return [d for d in deps_data if d['type'] == target_type]


class Deps(object):
    def __init__(self, direct_deps):
        self.direct_deps = direct_deps
        self.all_deps = get_all_deps(direct_deps)
        self.all_deps_data = get_deps_metadata(self.all_deps)

    def All(self, target_type):
        return get_deps_of_type(self.all_deps_data, target_type)


def write_meta_data(options, direct_deps):
    meta_data = {
        'root': {
            'type': options.type,
            'metadata_path': options.output,
            'metadata_deps': direct_deps
        }
    }
    root = meta_data['root']
    if options.type == 'app_profile':
        root[options.type] = options.app_profile
        root['resources'] = options.resources
    if options.type == 'js_assets':
        root[options.type] = options.js_assets
        if options.js_forms:
            root['js_forms'] = options.js_forms
        if options.testrunner:
            root['testrunner'] = options.testrunner
    if options.type == 'ets_assets':
        root[options.type] = options.ets_assets
    if options.type == 'assets':
        root[options.type] = options.raw_assets
    if options.type == 'unresolved_assets':
        root[options.type] = options.unresolved_assets
    if options.type == 'resources':
        deps = Deps(direct_deps)
        root[options.type] = options.resources
        package_name = options.package_name
        root['package_name'] = package_name if package_name else ""
        for target_type in ['app_profile']:
            for dep in deps.All(target_type):
                if root.get(target_type):
                    root.get(target_type).extend(dep[target_type])
                    root.get('resources').extend(dep['resources'])
                else:
                    root[target_type] = dep[target_type]
                    root['resources'] += dep['resources']
    if options.type == 'hap' or options.type == 'resources':
        hap_profile = options.hap_profile
        root['hap_profile'] = hap_profile if hap_profile else ""

    # Merge all metadata
    if options.type == 'hap':
        deps = Deps(direct_deps)
        root['hap_path'] = options.hap_path
        for target_type in ['js_assets', 'ets_assets', 'assets', 'resources']:
            root[target_type] = []
        if options.js_assets:
            root['js_assets'] = options.js_assets
        if options.ets_assets:
            root['ets_assets'] = options.ets_assets
        if options.raw_assets:
            root['assets'] = options.raw_assets
        if options.resources:
            root['resources'] = options.resources
        for target_type in ['js_assets', 'ets_assets', 'assets', 'resources', 'app_profile']:
            for dep in deps.All(target_type):
                if root.get(target_type):
                    root.get(target_type).extend(dep[target_type])
                    root.get('hap_profile').extend(dep['hap_profile'])
                else:
                    root[target_type] = dep[target_type]
                    if dep.get('hap_profile'):
                        root['hap_profile'] = dep['hap_profile']
                    if dep.get('js_forms'):
                        root['js_forms'] = dep['js_forms']
                    if dep.get('testrunner'):
                        root['testrunner'] = dep['testrunner']
        target_type = 'unresolved_assets'
        for dep in deps.All(target_type):
            if options.js2abc:
                if isinstance(dep[target_type], list):
                    for ability_path in dep[target_type]:
                        root.get('js_assets').append(ability_path)
                else:
                    root.get('js_assets').append(dep[target_type])
            else:
                if isinstance(dep[target_type], list):
                    for ability_path in dep[target_type]:
                        root.get('ets_assets').append(ability_path)
                else:
                    root.get('ets_assets').append(dep[target_type])
    build_utils.write_json(meta_data, options.output, only_if_changed=True)

# Collect assets entry according to config.json
def load_assets(options, assets, assets_type):
    pre_path = assets[0]
    pre_path = pre_path.rstrip('/')
    with open(options.hap_profile) as profile:
        config = json.load(profile)

        # In multi-ability cases, load the assets entry according to "srcPath" in config.json
        if os.path.basename(pre_path) == 'js' or os.path.basename(pre_path) == 'ets':
            assets = []
            for ability in config['module']['abilities']:
                if assets_type == 'js':
                    if ability.__contains__('srcPath') and ability.get('srcLanguage') == assets_type:
                        assets.append(os.path.join(pre_path, ability['srcPath']))

                    # Load js form entry according to "jsComponentName" in config.json
                    if ability.__contains__('forms'):
                        for form in ability['forms']:
                            if form.__contains__('jsComponentName'):
                                options.js_forms.append(os.path.join(pre_path, form['jsComponentName']))
                            else:
                                raise Exception('"module.abilities.ability.forms.form.jsComponentName" is required')
                else:
                    if ability.__contains__('srcPath'):
                        assets.append(os.path.join(pre_path, ability['srcPath']))
        else:
            pre_path = os.path.dirname(pre_path)

        # Load testrunner entry
        if config['module'].__contains__('testRunner') and assets_type == 'js':
            options.testrunner.append(os.path.join(pre_path, config['module']['testRunner']['srcPath']))
    if not assets:
        assets.append(pre_path)
    return assets

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--output',
                        help='output meta data file',
                        required=True)
    parser.add_argument('--type', help='type of module', required=True)
    parser.add_argument('--raw-assets', nargs='+', help='raw assets directory')
    parser.add_argument('--js-assets', nargs='+', help='js assets directory')
    parser.add_argument('--ets-assets', nargs='+', help='ets assets directory')
    parser.add_argument('--resources', nargs='+', help='resources directory')
    parser.add_argument('--hap-path', help='path to output hap')
    parser.add_argument('--depfile', help='path to .d file')
    parser.add_argument('--deps-metadata', nargs="+", help='metadata deps')
    parser.add_argument('--package-name',
                        help='package name for hap resources')
    parser.add_argument('--hap-profile', help='path to hap profile')
    parser.add_argument('--app-profile', help='path to app profile')
    parser.add_argument('--unresolved-assets', nargs='+', help='unresolved assets directory')
    parser.add_argument('--js2abc',
                        action='store_true',
                        default=False,
                        help='whether to transform js to ark bytecode')
    options = parser.parse_args()
    direct_deps = options.deps_metadata if options.deps_metadata else []

    # js forms entry list
    options.js_forms = []

    # testrunner entry list
    options.testrunner = []

    if options.hap_profile:
        if options.js_assets:
            options.js_assets = load_assets(options, options.js_assets, 'js')
        if options.ets_assets:
            options.ets_assets = load_assets(options, options.ets_assets, 'ets')
        if options.unresolved_assets:
            options.unresolved_assets = load_assets(options, options.unresolved_assets, 'unresolved')

    possible_input_strings = [
        options.type, options.raw_assets, options.js_assets, options.ets_assets, options.resources,
        options.hap_path, options.hap_profile, options.package_name, options.app_profile
    ]
    input_strings = [x for x in possible_input_strings if x]

    build_utils.call_and_write_depfile_if_stale(
        lambda: write_meta_data(options, direct_deps),
        options,
        depfile_deps=direct_deps,
        input_paths=direct_deps,
        input_strings=input_strings,
        output_paths=([options.output]),
        force=False,
        add_pydeps=False)


if __name__ == '__main__':
    sys.exit(main())
