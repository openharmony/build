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
    
    options, _ = parser.parse_args(args)
    options.resources_dir = build_utils.parse_gn_list(options.resources_dir)
    return options

def merge_profile(options):
    f3 = open(options.generated_profile, "w")
    with open(options.hap_profile) as f0:
        module_data = json.load(f0)["module"]
        with open(options.app_profile) as f1:
            app_data = json.load(f1)["app"]
            all_data = {}
            all_data["app"] = app_data
            all_data["module"] = module_data
            #json.dump(all_data, f0)
            f1.close()
        f0.close()
    json.dump(all_data, f3, indent=4, ensure_ascii=False)
    f3.close()
    shutil.copyfile(options.generated_profile, options.hap_profile)


def main(args):
    options = parse_args(args)
    if not options.app_profile:
        return
    #raise Exception("chenmudan merge error")
    #if not os.path.exists(options.app_profile):
    #    return

    inputs = ([options.app_profile, options.hap_profile])
    depfiles = []
    for directory in options.resources_dir:
        depfiles += (build_utils.get_all_files(directory))

    input_strings = [] #[options.package_name] if options.package_name else []
    outputs = [options.generated_profile]
#    merge_profile(options)
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
