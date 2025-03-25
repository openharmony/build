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
import json
from utils import (
    get_json,
    get_ninja_args,
    get_gn_args,
    is_enable_ccache,
    print_ccache_stats,
    clean_ccache_info,
    is_export_compile_commands,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_cmd(cmd: list):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8"
    )
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
    process_status = process.poll()
    if process_status:
        sys.exit(process_status)


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-v", "--variants", default=r".", type=str, help="variants of build target"
    )
    parser.add_argument(
        "-rp", "--root_path", default=r".", type=str, help="Path of root"
    )
    parser.add_argument(
        "-out",
        "--out_dir",
        default="src",
        type=str,
        help="the independent build out storage dir. default src , choices: src src_test or test",
    )
    parser.add_argument(
        "-t",
        "--test",
        default=1,
        type=int,
        help="whether the target contains test type. default 0 , choices: 0 or 1 2",
    )
    parser.add_argument("--fast-rebuild", action="store_true", help="run ninja only")
    args = parser.parse_args()
    return args


def _get_all_features_info(root_path, variants) -> list:
    _features_info_path = os.path.join(
        root_path, "out", "preloader", variants, "features.json"
    )
    args_list = []
    try:
        _features_json = get_json(_features_info_path)
        for key, value in _features_json.get("features").items():
            if isinstance(value, bool):
                args_list.append("{}={}".format(key, str(value).lower()))

            elif isinstance(value, str):
                args_list.append('{}="{}"'.format(key, value))

            elif isinstance(value, int):
                args_list.append("{}={}".format(key, value))

            elif isinstance(value, list):
                args_list.append('{}="{}"'.format(key, "&&".join(value)))

    except Exception as e:
        print("--_get_all_features_info json error--")

    return args_list


def _gn_cmd(root_path, variants, out_dir, test_filter):
    _features_info = _get_all_features_info(root_path, variants)
    _args_list = [f"ohos_indep_compiler_enable=true", f'product_name="{variants}"']
    _args_list.extend(_features_info)
    if is_enable_ccache():
        _args_list.append(f"ohos_build_enable_ccache=true")

    # Add 'use_thin_lto=false' to _args_list if test_filter equals 2
    if test_filter in (1, 2):
        _args_list.append("use_thin_lto=false")

    input_args = get_gn_args()
    _args_list.extend(input_args)

    _cmd_list = [
        f"{root_path}/prebuilts/build-tools/linux-x86/bin/gn",
        "gen",
        "--args={}".format(" ".join(_args_list)),
        "-C",
        f"out/{variants}/{out_dir}",
    ]
    if is_export_compile_commands():
        _cmd_list.append("--export-compile-commands")

    print(
        'Executing gn command: {} {} --args="{}" {}'.format(
            f"{root_path}/prebuilts/build-tools/linux-x86/bin/gn",
            "gen",
            " ".join(_args_list).replace('"', '\\"'),
            " ".join(_cmd_list[3:]),
        ),
        "info",
    )
    return _cmd_list


def _ninja_cmd(root_path, variants, out_dir):
    _cmd_list = [
        f"{root_path}/prebuilts/build-tools/linux-x86/bin/ninja",
        "-w",
        "dupbuild=warn",
        "-C",
        f"out/{variants}/{out_dir}",
    ]
    input_args = get_ninja_args()
    _cmd_list.extend(input_args)
    print("Executing ninja command: {}".format(" ".join(_cmd_list)))
    return _cmd_list


def _exec_cmd(root_path, variants, out_dir, test_filter, ninja_only=False):
    if not ninja_only:
        gn_cmd = _gn_cmd(root_path, variants, out_dir, test_filter)
        _run_cmd(gn_cmd)
    ninja_cmd = _ninja_cmd(root_path, variants, out_dir)
    clean_ccache_info()
    _run_cmd(ninja_cmd)
    print_ccache_stats()


def main():
    args = _get_args()
    variants = args.variants
    root_path = args.root_path
    out_dir = args.out_dir
    test_filter = args.test
    ninja_only = args.fast_rebuild
    _exec_cmd(root_path, variants, out_dir, test_filter, ninja_only)

    return 0


if __name__ == "__main__":
    sys.exit(main())
