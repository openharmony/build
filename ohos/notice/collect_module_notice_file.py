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

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from scripts.util.file_utils import read_json_file  # noqa: E402
from scripts.util import build_utils  # noqa: E402

README_FILE_NAME = 'README.OpenSource'


def is_top_dir(src_path):
    return os.path.exists(os.path.join(src_path, '.gn'))


def find_readme_in_pardir(pardir):
    if is_top_dir(pardir):
        return None
    for item in os.listdir(pardir):
        if os.path.isfile(item) and item == README_FILE_NAME:
            return os.path.join(pardir, item)
    return find_readme_in_pardir(os.path.dirname(pardir))


def get_notice_file_name(readme_file_path):
    contents = read_json_file(readme_file_path)
    if contents is None:
        raise Exception("Error: failed to read {}.".format(readme_file_path))

    notice = contents[0].get('License File')
    if notice is None:
        raise Exception("Error: failed to get notice file from {}.".format(
            readme_file_path))

    notice_path = os.path.join(os.path.dirname(readme_file_path), notice)

    if not os.path.exists(notice_path):
        print("Warning: notice file {} does not exist".format(notice_path))
        return None

    return notice_path


def get_readme_opensource(module_source_dir):
    expected = os.path.join(module_source_dir, README_FILE_NAME)
    if os.path.exists(expected):
        return expected
    else:
        return find_readme_in_pardir(os.path.dirname(module_source_dir))


def get_notice_file_path(module_source_dir):
    readme = os.path.join(module_source_dir, README_FILE_NAME)
    if not os.path.exists(readme):
        readme = None

    notice_file = None
    if readme:
        notice_file = get_notice_file_name(readme)
    return readme, notice_file


def do_collect_notice_files(options, depfiles):
    if options.notice_file is None:
        readme, notice_file = get_notice_file_path(options.module_source_dir)
        if readme:
            depfiles.append(readme)
    else:
        notice_file = options.notice_file
    if notice_file:
        for output in options.output:
            os.makedirs(os.path.dirname(output), exist_ok=True)
            shutil.copy(notice_file, output)
    else:
        for output in options.output:
            build_utils.touch(output)


def main(args):
    args = build_utils.expand_file_args(args)

    parser = argparse.ArgumentParser()
    build_utils.add_depfile_option(parser)

    parser.add_argument('--notice-file', help='', required=False)
    parser.add_argument('--output', action='append', required=False)
    parser.add_argument('--module-source-dir',
                        help='source directory of this module',
                        required=True)

    options = parser.parse_args()
    depfiles = []

    collect_notice_files(options, depfiles)
    if options.notice_file:
        depfiles.append(options.notice_file)
    build_utils.write_depfile(options.depfile, options.output[0], depfiles)


def collect_notice_files(options, depfiles):
    if 'third_party/' not in options.module_source_dir:
        if options.notice_file is None:
            for output in options.output:
                build_utils.touch(output)
            return

    do_collect_notice_files(options, depfiles)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
