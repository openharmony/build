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


def main():
    args = _get_args()
    root_path = args.root_path
    variants = args.variants
    variants_path = os.path.join(root_path, 'binarys', "variants", "variants_" + variants, "config")
    variants_out_path = os.path.join(root_path, 'out', "preloader", variants)
    etc_out_path = os.path.join(variants_out_path, "system", "etc")
    syscap_para_out_path = os.path.join(etc_out_path, "param")
    
    os.makedirs(syscap_para_out_path, exist_ok=True)

    system_capability_file = os.path.join(variants_path, "SystemCapability.json")
    features_file = os.path.join(variants_path, "features.json")
    build_file = os.path.join(variants_path, "build_config.json")
    paths_config_file = os.path.join(variants_path, "parts_config.json")
    syscap_json_file = os.path.join(variants_path, "syscap.json")
    syscap_para_file = os.path.join(variants_path, "syscap.para")

    shutil.copy(system_capability_file, etc_out_path)
    shutil.copy(syscap_json_file, etc_out_path)
    shutil.copy(syscap_para_file, syscap_para_out_path)
    shutil.copy(features_file, variants_out_path)
    shutil.copy(build_file, variants_out_path)
    shutil.copy(paths_config_file, variants_out_path)


if __name__ == '__main__':
    main()
