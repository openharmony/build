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

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file # noqa: E402


def check_parts_deps(args, external_part_name, parts_deps_info):
    compile_standard_allow_file = args.compile_standard_allow_file
    compile_standard_allow_info = read_json_file(compile_standard_allow_file)
    added_self_part_allow_list = compile_standard_allow_info.get("external_deps_added_self_part_module", [])
    bundle_not_add_allow_list = compile_standard_allow_info.get("external_deps_bundle_not_add", [])
    if external_part_name == args.part_name:
        message = "{} in target {} is dependency within part {}, Need to used deps".format(
            external_part_name, args.target_path, args.part_name)
        if args.target_path in added_self_part_allow_list:
            print(f"[0/0] WARNING: {message}")
            return
        else:
            raise Exception(message)

    _tips_info = "{} depend part {}, need set part deps info to".format(
        args.target_path, external_part_name)

    part_deps_info = parts_deps_info.get(args.part_name)
    if not part_deps_info:
        _warning_info = "{} {}.".format(_tips_info, args.part_name)
    elif not part_deps_info.get('components') or \
        not external_part_name in part_deps_info.get('components'):
        _warning_info = "{} {}.".format(_tips_info, part_deps_info.get('build_config_file'))
    else:
        _warning_info = ""

    if _warning_info != "":
        if args.target_path in bundle_not_add_allow_list:
            print(f"[0/0] WARNING: {_warning_info}")
        else:
            raise Exception(_warning_info)

    return


def check(args):
    depfiles = []
    if len(args.external_deps) == 0:
        return depfiles

    external_deps = args.external_deps

    parts_deps_file = 'build_configs/parts_info/parts_deps.json'
    parts_deps_info = read_json_file(parts_deps_file)
    if parts_deps_info is None:
        raise Exception("read pre_build parts_deps failed.")
    depfiles.append(parts_deps_file)

    for external_lib in external_deps:
        deps_desc = external_lib.split(':')
        external_part_name = deps_desc[0]
        check_parts_deps(args, external_part_name, parts_deps_info)

    return depfiles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--external-deps', nargs='*', required=True)
    parser.add_argument('--part-name', required=True, default='')
    parser.add_argument('--target-path', required=True, default='')
    parser.add_argument('--output', required=True, default='')
    args = parser.parse_args()

    check(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
