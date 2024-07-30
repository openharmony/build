#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
import subprocess
import sys
import argparse
import os
from utils import get_json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_cmd(cmd: list):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               encoding='utf-8')
    for line in iter(process.stdout.readline, ''):
        print(line)


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-v", "--variants", default=r".", type=str, help="variants of build target")
    parser.add_argument("-rp", "--root_path", default=r".", type=str, help="Path of root")
    args = parser.parse_args()
    return args


def _get_all_features_info(root_path) -> dict:
    _features_info_path = os.path.join(root_path, 'build', 'indep_configs', 'variants', 'default',
                                       'features.json')
    try:
        _features_json = get_json(_features_info_path)
    except Exception as e:
        print('--_get_all_features_info json error--')
    return _features_json.get('features')


def _gn_cmd(root_path, variants):
    _features_info = _get_all_features_info(root_path)
    _args_list = [f"ohos_indep_compiler_enable=true", f"product_name=\"{variants}\""]
    for k, v in _features_info.items():
        _args_list.append(f'{k}={str(v).lower()}')

    _args_info = ' '.join(_args_list)
    _cmd_list = [f'{root_path}/prebuilts/build-tools/linux-x86/bin/gn', 'gen', f'--args={_args_info}']
    _cmd_list += ['-C', f'out/{variants}']
    return _cmd_list


def _ninja_cmd(root_path, variants):
    _cmd_list = [f'{root_path}/prebuilts/build-tools/linux-x86/bin/ninja', '-w', 'dupbuild=warn', '-C',
                 f'out/{variants}']
    return _cmd_list


def _exec_cmd(root_path, variants):
    gn_cmd = _gn_cmd(root_path, variants)
    _run_cmd(gn_cmd)
    ninja_cmd = _ninja_cmd(root_path, variants)
    _run_cmd(ninja_cmd)


def main():
    args = _get_args()
    variants = args.variants
    root_path = args.root_path
    _exec_cmd(root_path, variants)

    return 0


if __name__ == '__main__':
    sys.exit(main())
