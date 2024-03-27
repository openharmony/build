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
import time
import stat
import utils


def _get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-p",
        "--input_path",
        default=r"./",
        type=str,
        help="Path of the folder where the collection of txt files to be processed is located.",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        default=r"./",
        type=str,
        help="path of output file. default: ./",
    )
    args = parser.parse_args()
    return args


def _scan_dir_to_get_info(bundle_path):
    dirs_info = dict()
    file_list = list()
    for entry in os.scandir(bundle_path):
        if entry.name == 'bundle.json':
            pass
        elif entry.is_dir():
            dirs_info.update({entry.name: [f"{entry.name}/*"]})
        elif entry.is_file():

            file_list.append(entry.name)
        else:
            print(f'{entry.name} is not file or dir ')
    dirs_info.update({"./": file_list})
    return dirs_info


def _out_bundle_json(bundle_json, file_name):
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(file_name, flags, modes), 'w') as f:
        json.dump(bundle_json, f, indent=2)


def main():
    args = _get_args()
    hpmcache_path = args.input_path
    dependences_file = os.path.join(hpmcache_path, 'dependences.json')
    dependences_json = utils.get_json(dependences_file)
    for part_name, part_info in dependences_json.items():
        part_path = part_info['installPath']
        bundle_path = os.path.join(hpmcache_path, part_path[1:], 'bundle.json')
        bundle_json = utils.get_json(bundle_path)
        dirs_info = _scan_dir_to_get_info(os.path.join(hpmcache_path, part_path[1:]))
        bundle_json.update({"dirs": dirs_info})
        _out_bundle_json(bundle_json, bundle_path)


if __name__ == '__main__':
    main()
