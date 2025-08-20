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

import os
import sys
import argparse

import check_deps_handler
import check_external_deps
import check_part_subsystem_name

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.util.build_utils import write_depfile, add_depfile_option, touch  # noqa: E402
from scripts.util.file_utils import read_json_file  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()
    add_depfile_option(parser)
    parser.add_argument("--skip-check-subsystem", required=False, action="store_true")
    parser.add_argument('--part-name', required=True)
    parser.add_argument('--subsystem-name', required=True)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--target-path', required=True)
    parser.add_argument('--deps', nargs='*', required=False)
    parser.add_argument('--external-deps', nargs='*', required=False)
    parser.add_argument('--output', required=True)
    parser.add_argument('--compile-standard-allow-file', required=True)
    args = parser.parse_args()

    return args


def get_depfile_info(part_name: str, source_root_dir: str) -> list:
    depfile = []
    parts_path_file = 'build_configs/parts_info/parts_path_info.json'
    parts_path_info = read_json_file(parts_path_file)
    if not parts_path_info:
        raise Exception("read pre_build parts_path_info failed")

    part_path = parts_path_info.get(part_name)
    if not part_path:
        return depfile

    bundle_json_file = os.path.join(source_root_dir, part_path, "bundle.json")
    if os.path.exists(bundle_json_file):
        depfile.append(bundle_json_file)

    return depfile


def main():
    args = parse_args()

    add_depfile = False
    if not args.skip_check_subsystem:
        check_part_subsystem_name.check(args)
        add_depfile = True

    if args.deps:
        check_deps_handler.check(args)
        add_depfile = True

    if args.external_deps:
        check_external_deps.check(args)
        add_depfile = True

    depfiles = []
    if add_depfile:
        depfiles.extend(get_depfile_info(args.part_name, args.source_root_dir))

    if args.depfile:
        write_depfile(args.depfile, args.output, depfiles, add_pydeps=False)

    touch(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
