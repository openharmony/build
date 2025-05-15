#!/usr/bin/env python
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
from concurrent.futures import ThreadPoolExecutor
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from scripts.util.file_utils import read_json_file, write_json_file  # noqa: E402 E501
from util.log_util import LogUtil
from scripts.util.detect_cpu_count import get_cpu_count

_default_subsystem = {"build": "build"}


@throw_exception
def _read_config(subsystem_config_file, example_subsystem_file):
    if not os.path.exists(subsystem_config_file):
        raise OHOSException(
            "config file '{}' doesn't exist.".format(subsystem_config_file), "2013")
    subsystem_config = read_json_file(subsystem_config_file)
    if subsystem_config is None:
        raise OHOSException("read file '{}' failed.".format(
            subsystem_config_file), "2013")

    # example subsystem
    if example_subsystem_file:
        example_subsystem_config = read_json_file(example_subsystem_file)
        if example_subsystem_config is not None:
            subsystem_config.update(example_subsystem_config)

    subsystem_info = {}
    for key, val in subsystem_config.items():
        if 'path' not in val:
            raise OHOSException(
                "subsystem '{}' not config path.".format(key), "2013")
        subsystem_info[key] = val.get('path')
    return subsystem_info


def _scan_build_file(subsystem_path):
    _files = []
    _bundle_files = []
    for root, dirs, files in os.walk(subsystem_path):
        for name in files:
            if name == 'ohos.build':
                _files.append(os.path.join(root, name))
            elif name == 'bundle.json':
                _bundle_files.append(os.path.join(root, name))
    if _bundle_files:
        _files.extend(_bundle_files)
    return _files


def _check_path_prefix(paths):
    allow_path_prefix = ['vendor', 'device']
    result = list(
        filter(lambda x: x is False,
               map(lambda p: p.split('/')[0] in allow_path_prefix, paths)))
    return len(result) <= 1


def scan_task(args):
    key, paths = args
    _all_build_config_files = []
    for _subsystem_path in paths:
        _all_build_config_files.extend(_scan_build_file(_subsystem_path))
    return key, _all_build_config_files


@throw_exception
def scan(subsystem_config_file, example_subsystem_file, source_root_dir):
    subsystem_infos = _read_config(subsystem_config_file,
                                   example_subsystem_file)
    # add common subsystem info
    subsystem_infos.update(_default_subsystem)

    no_src_subsystem = {}
    _build_configs = {}
    scan_tasks = []

    for key, val in subsystem_infos.items():
        _all_build_config_files = []
        if not isinstance(val, list):
            val = [val]
        else:
            if not _check_path_prefix(val):
                raise OHOSException(
                    "subsystem '{}' path configuration is incorrect.".format(
                        key), "2013")
        subsystem_paths = [os.path.join(source_root_dir, _path) for _path in val]
        scan_tasks.append((key, subsystem_paths))
    try:
        cpu_cap = get_cpu_count()
    except OSError:
        cpu_cap = 8
    thread_num = cpu_cap * 2
    LogUtil.hb_info(f'The thread num for subsytem config scan is {thread_num}')
    with ThreadPoolExecutor(max_workers=thread_num) as executor:
        results = list(executor.map(scan_task, scan_tasks))
    for key, build_files in results:
        if build_files:
            _build_configs[key] = {
                "path": list(subsystem_infos[key] if isinstance(subsystem_infos[key], list) else [subsystem_infos[key]]),
                "build_files": build_files
            }
        else:
            no_src_subsystem[key] = list(subsystem_infos[key] if isinstance(subsystem_infos[key], list) else [subsystem_infos[key]])

    scan_result = {
        'source_path': source_root_dir,
        'subsystem': _build_configs,
        'no_src_subsystem': no_src_subsystem
    }

    LogUtil.hb_info('subsytem config scan completed')
    return scan_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subsystem-config-file', required=True)
    parser.add_argument('--subsystem-config-overlay-file', required=True)
    parser.add_argument('--example-subsystem-file', required=False)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

    build_configs = scan(args.subsystem_config_file,
                         args.example_subsystem_file, args.source_root_dir)

    build_configs_file = os.path.join(args.output_dir,
                                      "subsystem_build_config.json")
    write_json_file(build_configs_file, build_configs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
