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
import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from scripts.util.file_utils import read_json_file, write_json_file  # noqa: E402 E501
from util.log_util import LogUtil
from util.progress_spinner import progress_spinner
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


def _scan_build_file(subsystem_path, enable_depth_optimization):
    _files = []
    _bundle_files = []
    _ignore_dirs = [ '.git', '.gitee', '.github', 'doc', 'docs', 'node_modules']
    max_depth = 5
    bundle_dirs = set()

    for root, dirs, files in os.walk(subsystem_path):
        dirs[:] = [d for d in dirs if d not in _ignore_dirs]
        for name in files:
            if name == 'ohos.build':
                _files.append(os.path.join(root, name))
                bundle_dirs.add(root)
            elif name == 'bundle.json':
                _bundle_files.append(os.path.join(root, name))
                bundle_dirs.add(root)

        current_depth = root[len(os.path.normpath(subsystem_path)):].count(os.sep)
        if enable_depth_optimization and current_depth >= max_depth:
            for _bundle_dir in bundle_dirs:
                _bundle_dir += os.sep
                if root.startswith(_bundle_dir):
                    del dirs[:]
                    break

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
    key, path, enable_optimization = args
    _all_build_config_files = []
    _all_build_config_files.extend(_scan_build_file(path, enable_optimization))
    return key, _all_build_config_files


@throw_exception
@progress_spinner("subsystem config scanning ...")
def scan_subsystem_info(source_root_dir, subsystem_infos, enable_scan_optimization):
    scan_tasks = []

    for key, val in subsystem_infos.items():
        if not isinstance(val, list):
            val = [val]
        else:
            if not _check_path_prefix(val):
                raise OHOSException(
                    "subsystem '{}' path configuration is incorrect.".format(
                        key), "2013")
        for _path in val:
            subsystem_path = os.path.join(source_root_dir, _path)
            scan_tasks.append((key, subsystem_path, enable_scan_optimization))

    with multiprocessing.Pool() as pool:
        results = list(pool.imap_unordered(scan_task, scan_tasks, chunksize=1))

    return results


def scan(subsystem_config_file, example_subsystem_file, source_root_dir, enable_scan_optimization):
    s_time = time.monotonic()
    subsystem_infos = _read_config(subsystem_config_file,
                                   example_subsystem_file)
    # add common subsystem info
    subsystem_infos.update(_default_subsystem)

    no_src_subsystem = {}
    _build_configs = {}
    results = scan_subsystem_info(source_root_dir, subsystem_infos, enable_scan_optimization)

    merged = {}
    for key, build_files in results:
        merged.setdefault(key, [])
        merged[key].extend(build_files)

    for key, build_files in merged.items():
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

    e_time = time.monotonic()
    LogUtil.hb_info('subsytem config scan completed costed is {} s'.format(round(e_time - s_time, 2)))
    return scan_result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subsystem-config-file', required=True)
    parser.add_argument('--subsystem-config-overlay-file', required=True)
    parser.add_argument('--example-subsystem-file', required=False)
    parser.add_argument('--source-root-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--enable-scan-optimization', action='store_true')
    args = parser.parse_args()

    build_configs = scan(args.subsystem_config_file,
                         args.example_subsystem_file, args.source_root_dir, args.enable_scan_optimization)

    build_configs_file = os.path.join(args.output_dir,
                                      "subsystem_build_config.json")
    write_json_file(build_configs_file, build_configs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
