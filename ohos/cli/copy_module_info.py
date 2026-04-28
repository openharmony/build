#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Huawei Device Co., Ltd.
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
import shutil
import sys


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Copy module_info.json file")
    parser.add_argument("--src", required=True, help="Source file path")
    parser.add_argument("--dst", required=True, help="Destination file path")
    return parser


def ensure_parent_dir(path: str) -> None:
    dst_dir = os.path.dirname(path)
    if dst_dir and not os.path.exists(dst_dir):
        os.makedirs(dst_dir)


def main() -> int:
    args = build_argument_parser().parse_args()

    try:
        ensure_parent_dir(args.dst)
        shutil.copy2(args.src, args.dst)
        return 0
    except Exception as exc:
        print(f"Error copying file: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
