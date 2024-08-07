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
import argparse
import os
import shutil
import stat

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from scripts.util.file_utils import read_json_file, write_json_file  # noqa: E402
from scripts.util import build_utils  # noqa: E402

README_FILE_NAME = 'README.OpenSource'
LICENSE_CANDIDATES = [
    'LICENSE',
    'License',
    'NOTICE',
    'Notice',
    'COPYRIGHT',
    'Copyright',
    'COPYING',
    'Copying',
    'AUTHORS'
]


def is_top_dir(current_dir: str):
    return os.path.exists(os.path.join(current_dir, '.gn'))


def find_other_files(license_file_path):
    other_files = []
    if os.path.isfile(license_file_path):
        license_dir = os.path.dirname(license_file_path)
        license_file = os.path.basename(license_file_path)
        for file in LICENSE_CANDIDATES:
            license_path = os.path.join(license_dir, file)
            if os.path.isfile(license_path) and file != license_file and \
                    license_path not in other_files:
                other_files.append(license_path)
    elif os.path.isdir(license_file_path):
        for file in ['COPYRIGHT', 'Copyright', 'COPYING', 'Copying', 'AUTHORS']:
            license_file = os.path.join(license_file_path, file)
            if os.path.isfile(license_file):
                other_files.append(license_file)
    return other_files


def find_license_recursively(current_dir: str):
    if is_top_dir(current_dir):
        return None
    for file in LICENSE_CANDIDATES:
        candidate = os.path.join(current_dir, file)
        if os.path.isfile(os.path.join(current_dir, file)):
            return os.path.join(candidate)
    return find_license_recursively(os.path.dirname(current_dir))


def find_opensource_recursively(current_dir: str):
    if is_top_dir(current_dir):
        return None
    candidate = os.path.join(current_dir, README_FILE_NAME)
    if os.path.isfile(candidate):
        return os.path.join(candidate)
    return find_opensource_recursively(os.path.dirname(current_dir))


def get_license_from_readme(readme_path: str):
    contents = read_json_file(readme_path)
    if contents is None:
        raise Exception("Error: failed to read {}.".format(readme_path))

    notice_file = contents[0].get('License File').strip()
    notice_name = contents[0].get('Name').strip()  
    notice_version = contents[0].get('Version Number').strip()
    if notice_file is None:
        raise Exception("Error: value of notice file is empty in {}.".format(
            readme_path))
    if notice_name is None:
        raise Exception("Error: Name of notice file is empty in {}.".format(
            readme_path))
    if notice_version is None:
        raise Exception("Error: Version Number of notice file is empty in {}.".format(
            readme_path))

    return os.path.join(os.path.dirname(readme_path), notice_file), notice_name, notice_version


def do_collect_notice_files(options, depfiles: str):
    module_notice_info_list = []
    module_notice_info = {}
    notice_file = options.license_file
    other_files = []
    if notice_file:
        opensource_file = find_opensource_recursively(os.path.abspath(options.module_source_dir))
        if opensource_file is not None and os.path.exists(opensource_file):
            other_files.extend(find_other_files(opensource_file))
            notice_file_info = get_license_from_readme(opensource_file)
            module_notice_info['Software'] = "{}".format(notice_file_info[1])
            module_notice_info['Version'] = "{}".format(notice_file_info[2])
        else:
            module_notice_info['Software'] = ""
            module_notice_info['Version'] = ""
    if notice_file is None:
        readme_path = os.path.join(options.module_source_dir,
                                   README_FILE_NAME)
        if not os.path.exists(readme_path):
            readme_path = find_opensource_recursively(os.path.abspath(options.module_source_dir))
        if readme_path is not None:
            depfiles.append(readme_path)
            notice_file_info = get_license_from_readme(readme_path)
            notice_file = notice_file_info[0]
            notice_dir = os.path.dirname(readme_path)
            other_files.extend(find_other_files(os.path.join(notice_dir, notice_file)))
            module_notice_info['Software'] = "{}".format(notice_file_info[1])
            module_notice_info['Version'] = "{}".format(notice_file_info[2])

    if notice_file is None:
        notice_file = find_license_recursively(options.module_source_dir)
        opensource_file = find_opensource_recursively(os.path.abspath(options.module_source_dir))
        if opensource_file is not None and os.path.exists(opensource_file):
            other_files.extend(find_other_files(opensource_file))
            notice_file_info = get_license_from_readme(opensource_file)
            module_notice_info['Software'] = "{}".format(notice_file_info[1])
            module_notice_info['Version'] = "{}".format(notice_file_info[2])
        else:
            module_notice_info['Software'] = ""
            module_notice_info['Version'] = ""
    
    if module_notice_info['Software']:
        module_notice_info['Path'] = "/{}".format(options.module_source_dir[5:])
        module_notice_info_list.append(module_notice_info)

    if notice_file:
        if other_files:
            notice_file = f"{notice_file},{','.join(other_files)}"
        for output in options.output:
            notice_info_json = '{}.json'.format(output)
            os.makedirs(os.path.dirname(output), exist_ok=True)
            os.makedirs(os.path.dirname(notice_info_json), exist_ok=True)
            notice_files = notice_file.split(",")
            write_file_content(notice_files, options, output, notice_info_json, module_notice_info_list, depfiles)


def write_file_content(notice_files, options, output, notice_info_json, module_notice_info_list, depfiles):
    notice_files = [file for file in notice_files if file]
    for notice_file in notice_files:
        notice_file = notice_file.strip()
        if not os.path.exists(notice_file):
            notice_file = os.path.join(options.module_source_dir, notice_file)
        if os.path.exists(notice_file):
            if not os.path.exists(output):
                build_utils.touch(output)
            write_notice_to_output(notice_file, output)
            write_json_file(notice_info_json, module_notice_info_list)
        else:
            build_utils.touch(output)
            build_utils.touch(notice_info_json)
        depfiles.append(notice_file)


def write_notice_to_output(notice_file, output):
    with os.fdopen(os.open(notice_file, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8', errors='ignore') as notice_data_flow:
        license_content = notice_data_flow.read()
    with os.fdopen(os.open(output, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                   'r', encoding='utf-8', errors='ignore') as output_data_flow:
        output_file_content = output_data_flow.read()
    if license_content not in output_file_content:
        with os.fdopen(os.open(output, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR),
                       'a', encoding='utf-8') as testfwk_info_file:
            testfwk_info_file.write(f"{license_content}\n")
            testfwk_info_file.close()


def main(args):
    args = build_utils.expand_file_args(args)

    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--license-file', required=False)
    parser.add_argument('--output', action='append', required=False)
    parser.add_argument('--sources', action='append', required=False)
    parser.add_argument('--sdk-install-info-file', required=False)
    parser.add_argument('--label', required=False)
    parser.add_argument('--sdk-notice-dir', required=False)
    parser.add_argument('--module-source-dir',
                        help='source directory of this module',
                        required=True)

    options = parser.parse_args()
    depfiles = []

    if options.sdk_install_info_file:
        install_dir = ''
        sdk_install_info = read_json_file(options.sdk_install_info_file)
        for item in sdk_install_info:
            if options.label == item.get('label'):
                install_dir = item.get('install_dir')
                break
        if options.sources and install_dir:
            for src in options.sources:
                extend_output = os.path.join(options.sdk_notice_dir, install_dir,
                                             '{}.{}'.format(os.path.basename(src), 'txt'))
                options.output.append(extend_output)

    do_collect_notice_files(options, depfiles)
    if options.license_file:
        depfiles.append(options.license_file)
    build_utils.write_depfile(options.depfile, options.output[0], depfiles)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

