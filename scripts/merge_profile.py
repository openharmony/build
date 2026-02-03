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

from email.policy import default
import optparse
import os
import stat
import sys
import shutil
import json

from zipfile import ZipFile  # noqa: E402
from util import build_utils  # noqa: E402


def parse_args(args):
    args = build_utils.expand_file_args(args)

    parser = optparse.OptionParser()
    build_utils.add_depfile_option(parser)
    parser.add_option('--resources-dir', help='resources directory')
    parser.add_option('--app-profile', default=False, help='path to app profile')
    parser.add_option('--hap-profile', help='path to hap profile')
    parser.add_option('--generated-profile', help='path to generated profile')
    parser.add_option('--release-type', help='release type')
    parser.add_option('--api-version', help='api version')
    options, _ = parser.parse_args(args)
    options.resources_dir = build_utils.parse_gn_list(options.resources_dir)
    return options


def merge_profile(options):
    all_data = {}
    with open(options.hap_profile) as f0:
        if len(options.app_profile) == 0:
            all_data = json.load(f0)
        else:
            module_data = json.load(f0)["module"]
            with open(options.app_profile) as f1:
                app_data = json.load(f1)["app"]
                all_data["app"] = app_data
                all_data["module"] = module_data
                f1.close()
        f0.close()
    if str(all_data.get('app').get('targetAPIVersion')) == options.api_version:
        all_data["app"]["apiReleaseType"] = options.release_type
    else:
        all_data["app"]["apiReleaseType"] = 'Release'
    with os.fdopen(os.open(options.generated_profile,
                            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                            stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH),
                    'w') as f3:
        json.dump(all_data, f3, indent=4, ensure_ascii=False)


def main(args):
    options = parse_args(args)
    inputs = [options.hap_profile]
    if not options.app_profile:
        inputs += options.app_profile
    depfiles = []
    for directory in options.resources_dir:
        depfiles += (build_utils.get_all_files(directory))

    input_strings = []
    outputs = [options.generated_profile]
    build_utils.call_and_write_depfile_if_stale(
        lambda: merge_profile(options),
        options,
        depfile_deps=depfiles,
        input_paths=inputs + depfiles,
        input_strings=input_strings,
        output_paths=(outputs),
        force=False,
        add_pydeps=False)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
