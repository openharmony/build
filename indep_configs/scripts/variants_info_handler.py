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

import argparse
import json
import os
import shutil
import stat
import time
import utils


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-rp",
        "--root_path",
        default=r".",
        type=str,
        help="Path of root",
    )
    parser.add_argument(
        "-v",
        "--variants",
        default=r".",
        type=str,
        help="variants of build target",
    )
    args = parser.parse_args()
    return args


def _gen_syscap_para_info(variants_path, syscap_out_path):
    syscap_json_file = os.path.join(variants_path, 'syscap.json')
    syscap_json = utils.get_json(syscap_json_file)
    syscap_value = syscap_json.get('syscap_value')
    os.makedirs(syscap_out_path)
    out_path = os.path.join(syscap_out_path, 'syscap.para')

    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    try:
        with os.fdopen(os.open(out_path, flags, modes), 'w') as f:
            for k, v in syscap_value.items():
                f.write(f'{k}={str(v).lower()}' + '\n')
    except Exception as e:
        print(f"{out_path}: \n {e}")
    return syscap_json


def _re_gen_syscap_json(syscap_json, variants_out_path):
    syscap_json_out_file = os.path.join(variants_out_path, "syscap.json")

    del syscap_json['syscap_value']
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(syscap_json_out_file, flags, modes), 'w') as f:
        json.dump(syscap_json, f, indent=4)


def main():
    args = _get_args()
    root_path = args.root_path
    variants = args.variants
    variants_path = os.path.join(root_path, 'build', 'indep_configs', "variants", variants)
    variants_out_path = os.path.join(root_path, 'out', "preloader", variants)
    etc_out_path = os.path.join(variants_out_path, "system", "etc")
    syscap_out_path = os.path.join(etc_out_path, "param")
    
    re_syscap_json = _gen_syscap_para_info(variants_path, syscap_out_path)
    _re_gen_syscap_json(re_syscap_json, etc_out_path)

    system_capability_file = os.path.join(variants_path, "SystemCapability.json")
    features_file = os.path.join(variants_path, "features.json")
    build_file = os.path.join(variants_path, "build_config.json")
    paths_config_file = os.path.join(variants_path, "parts_config.json")

    shutil.copy(system_capability_file, etc_out_path)
    shutil.copy(features_file, variants_out_path)
    shutil.copy(build_file, variants_out_path)
    shutil.copy(paths_config_file, variants_out_path)


if __name__ == '__main__':
    main()
