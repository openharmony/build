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
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.build_utils import write_depfile, add_depfile_option, touch  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()
    add_depfile_option(parser)
    parser.add_argument("--skip-check-subsystem", required=False, action="store_true")
    parser.add_argument('--part-name', required=True)
    parser.add_argument('--subsystem-name', required=True)
    parser.add_argument('--target-path', required=True)
    parser.add_argument('--deps', nargs='*', required=False)
    parser.add_argument('--external-deps', nargs='*', required=False)
    parser.add_argument('--output', required=True)
    parser.add_argument('--compile-standard-allow-file', required=True)
    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    depfiles = []
    if not args.skip_check_subsystem:
        _depfile = check_part_subsystem_name.check(args)
        depfiles.extend(_depfile)

    if args.deps:
        _depfile = check_deps_handler.check(args)
        depfiles.extend(_depfile)

    if args.external_deps:
        _depfile = check_external_deps.check(args)
        depfiles.extend(_depfile)

    if depfiles:
        depfiles = list(set(depfiles))
        write_depfile(args.depfile, args.output, depfiles)

    touch(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
