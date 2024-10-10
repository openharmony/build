#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Device Co., Ltd.
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
import os
import shutil
import tarfile
import argparse
from util import build_utils

sys.path.append(
    os.path.abspath(os.path.dirname(os.path.abspath(
        os.path.dirname(__file__)))))
from scripts.util.file_utils import read_json_file  # noqa: E402

RELEASE_FILENAME = 'README.OpenSource'


def _copy_opensource_file(opensource_config_file: str, top_dir: str, package_dir: str) -> bool:
    if not os.path.exists(opensource_config_file):
        print("Warning, the opensource config file is not exists.")
        return False

    src_dir = os.path.dirname(opensource_config_file)
    dst_dir = os.path.join(package_dir, os.path.relpath(src_dir, top_dir))

    # copy opensource folder to out dir
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir,
                    dst_dir,
                    symlinks=True,
                    ignore=shutil.ignore_patterns('*.pyc', 'tmp*', '.git*'))

    # delete the README.OpenSource file
    release_file = os.path.join(dst_dir, RELEASE_FILENAME)
    os.remove(release_file)
    return True


def _parse_opensource_file(opensource_config_file: str, license_set: set) -> bool:
    if not os.path.exists(opensource_config_file):
        print("Warning, the opensource config file is not exists.")
        return False

    opensource_config = read_json_file(opensource_config_file)
    if opensource_config is None:
        raise Exception("read opensource config file [{}] failed.".format(
            opensource_config_file))

    result = False
    for info in opensource_config:
        _license = info.get('License')
        # any license in collect list is collected
        if any(lic in _license for lic in license_set):
            result = True
            break

    return result


def _scan_and_package_code_release(scan_dir: str, top_dir: str, package_dir: str, license_set: set):
    file_dir_names = os.listdir(scan_dir)
    for file_dir_name in file_dir_names:
        file_dir_path = os.path.join(scan_dir, file_dir_name)
        if os.path.isdir(file_dir_path) and not os.path.islink(file_dir_path):
            _scan_and_package_code_release(file_dir_path, top_dir, package_dir, license_set)
        elif file_dir_path == os.path.join(scan_dir, RELEASE_FILENAME):
            if _parse_opensource_file(file_dir_path, license_set):
                _copy_opensource_file(file_dir_path, top_dir, package_dir)


def _collect_opensource(options, package_dir: str):
    # get the source top directory to be scan
    top_dir = options.root_dir

    # processing scan dir and license, split by colon
    scan_dir_list = options.scan_dirs.split(":")
    if not scan_dir_list:
        raise Exception("empty scan dir, please check the value of osp_scan_dirs.")
    scan_licenses = options.scan_licenses.split(":")
    if not scan_licenses:
        raise Exception("empty scan licenses, please check the value of osp_scan_licenses.")

    # scan the target dir and copy release code to out/opensource dir
    # remove duplicate scan dir
    dir_set = set([os.path.join(top_dir, _dir) for _dir in scan_dir_list])
    # remove duplicate licenses
    license_set = set(scan_licenses)
    for scan_dir in dir_set:
        if not os.path.isdir(scan_dir):
            raise Exception(f"{scan_dir} not exist, this is invalid.")
        _scan_and_package_code_release(scan_dir, top_dir, package_dir, license_set)


def _tar_opensource_package_file(options, package_dir: str) -> int:
    result = -1
    if os.path.exists(package_dir):
        try:
            with tarfile.open(options.output, "w:gz") as tar:
                tar.add(package_dir, arcname=".")
                result = 0
        except IOError as err:
            raise err
    return result


def main(args) -> int:
    """generate open source packages to release."""
    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)
    parser.add_argument('--output', required=True, help='output')
    parser.add_argument('--root-dir', required=True, help='source root directory')
    parser.add_argument('--scan-dirs', required=True, help='extended scan directory')
    parser.add_argument('--scan-licenses', required=True, help='extended scan licenses')

    # add optional extended parameters
    parser.add_argument('--only-collect-file', action='store_true', help='need post process, only collect file')

    options = parser.parse_args(args)

    # need post process, only collection is required
    if options.only_collect_file:
        package_dir = os.path.dirname(options.output)
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        os.makedirs(package_dir, exist_ok=True)
        _collect_opensource(options, package_dir)
        build_utils.touch(options.output)
        return 0

    with build_utils.temp_dir() as package_dir:
        _collect_opensource(options, package_dir)
        # package the opensource to Code_Opensource.tar.gz
        if _tar_opensource_package_file(options, package_dir) == 0:
            print('Generate the opensource package successfully.')
        else:
            print('Generate the opensource package failed.')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
