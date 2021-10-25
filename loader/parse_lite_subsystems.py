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

import argparse
import sys
import json
import os


def parse_lite_components(file):
    subsytem_name = os.path.basename(file)[:-5]
    configs = {}
    configs['subsystem_name'] = subsytem_name
    with open(file, 'rb') as fin:
        data = json.load(fin)
        components = data.get('components')
        parts = {}
        for com in components:
            part = {}
            targets = com.get('targets')
            test_targets = []
            non_test_targets = []
            for item in targets:
                target_names = item.strip('"').split(':')
                if len(target_names) > 1 and 'test' in target_names[1]:
                    test_targets.append(item)
                else:
                    non_test_targets.append(item)
            part['module_list'] = non_test_targets
            if test_targets != []:
                part['test_list'] = test_targets
            part_name = com.get('component')
            parts[part_name] = part
        configs['parts'] = parts
    return configs


def save_as_ohos_build(config, ohos_build):
    new_config = json.dumps(config, indent=2, sort_keys=True)
    with open(ohos_build, 'w') as fout:
        fout.write(new_config)


def parse(source_root_dir, lite_components_dir, build_configs_dir,
          subsystem_config_file):
    os.makedirs(build_configs_dir, exist_ok=True)

    subsystem_config = {}
    with open(subsystem_config_file, 'r') as fin:
        subsystem_config = json.load(fin)

    subsystem_infos = {}
    for root, _, files in os.walk(lite_components_dir):
        for file in files:
            if file == 'vendor.json':
                continue
            if file[-5:] == '.json':
                configs = parse_lite_components(os.path.join(root, file))
                subsystem_name = configs.get('subsystem_name')
                ohos_build = os.path.join(build_configs_dir,
                                          '{}.build'.format(subsystem_name))
                save_as_ohos_build(configs, ohos_build)
                info = {}
                info['build_files'] = [ohos_build]
                info['path'] = subsystem_config.get(subsystem_name).get('path')
                subsystem_infos[subsystem_name] = info
    return {
        'source_path': source_root_dir,
        'subsystem': subsystem_infos,
        'no_src_subsystem': {}
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-configs-dir', required=True)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--subsystem-config-file', required=True)
    parser.add_argument('--lite-components-dir', required=True)
    options = parser.parse_args()
    parse(options.source_root_dir, options.lite_components_dir,
          options.build_configs_dir, options.subsystem_config_file)


if __name__ == '__main__':
    sys.exit(main())
