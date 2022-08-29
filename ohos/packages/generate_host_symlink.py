#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from scripts.util.file_utils import read_json_file, write_json_file  # noqa: E402


def _do_symlink(all_host_parts_info, output_file, root_build_dir):
    output_result = {}
    for part_info in all_host_parts_info:
        part_info_file = part_info.get('part_info_file')
        part_modules_host_info = read_json_file(part_info_file)
        for info in part_modules_host_info:
            if info:
                module_def = info.get('module_def')
                module_info_file = info.get('module_info_file')
                module_info = read_json_file(module_info_file)
                if 'symlink' in module_info:
                    source_file = module_info.get('source')
                    source_file = os.path.join(root_build_dir, source_file)
                    symlink_dest = module_info.get('symlink')
                    
                    for name in symlink_dest:
                        symlink_dest_dir = os.path.dirname(source_file)
                        symlink_dest_file = os.path.join(root_build_dir, symlink_dest_dir, name)
                        if not os.path.exists(symlink_dest_file):
                            os.symlink(source_file, symlink_dest_file)
                            output_result[symlink_dest_file] = str(source_file)
    write_json_file(output_file, output_result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all-parts-host-info-file', required=True)
    parser.add_argument('--output-file', required=True)
    parser.add_argument('--root-build-dir', required=True)
    args = parser.parse_args()
    all_host_parts_info = read_json_file(args.all_parts_host_info_file)
    _do_symlink(all_host_parts_info, args.output_file, args.root_build_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
