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

import argparse
import json
import os
import sys
import shutil


def get_hap_module_info(build_target_name, module_name,
                            testcases_dir, subsystem_name,
                            part_name, project_path):
    if not build_target_name or not module_name:
        raise ValueError(
            'Ethire build_target_name or module_name is invalid')
    if os.path.exists(os.path.join(project_path, "Test.json")):
        module_info_file = os.path.join(testcases_dir, module_name + '.moduleInfo')

        if os.path.exists(module_info_file):
            return
        module_info_data = {'subsystem': subsystem_name, 'part': part_name,
                            'module': module_name}
        with open(module_info_file, 'w') as out_file:
            json.dump(module_info_data, out_file)


def get_hap_json_info(project_path, build_target_name,
                      archive_testfile, test_type, module_out_path):
    json_dir = os.path.dirname(archive_testfile)
    prefix_dir = os.path.join(test_type, module_out_path)
    if os.path.exists(os.path.join(project_path, "Test.json")):
        shutil.copy2(os.path.join(project_path, "Test.json"),
                     os.path.join(json_dir, (build_target_name + ".json")))
        json_file_path = os.path.join(json_dir, (build_target_name + ".json"))
        if os.path.exists(json_file_path):
            with open(json_file_path, "r") as out_file:
                json_data = json.load(out_file)
            if "kits" in json_data.keys():
                kits_list = json_data.get("kits")
                for kits_dict in kits_list:
                    if "push" in kits_dict:
                        push_list = kits_dict.get("push")
                        push_list = [
                            os.path.join(prefix_dir, push_key)
                            if prefix_dir not in push_key else push_key
                            for push_key in push_list
                        ]
                        kits_dict["push"] = push_list
                    if "test-file-name" in kits_dict:
                        test_file_name_list = kits_dict.get("test-file-name")
                        test_file_name_list = [
                            os.path.join(prefix_dir, file_key)
                            if prefix_dir not in file_key else file_key
                            for file_key in test_file_name_list
                        ]
                        kits_dict["test-file-name"] = test_file_name_list

            json_str = json.dumps(json_data, indent=2)
            with open(json_file_path, "w") as json_file:
                json_file.write(json_str)


def copy_hap_case(final_hap_path, archive_testfile):
    archive_testfile_dir = os.path.dirname(archive_testfile)
    shutil.copy2(final_hap_path, archive_testfile_dir)
    shutil.copy2(final_hap_path + ".md5.stamp", archive_testfile_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build_target_name', help='', required=True)
    parser.add_argument('--subsystem_name', help='', required=True)
    parser.add_argument('--archive_testfile', help='', required=True)
    parser.add_argument('--part_name', help='', required=True)
    parser.add_argument('--project_path', help='', required=True)
    parser.add_argument('--final_hap_path', help='', required=True)
    parser.add_argument('--test_type', help='', required=True)
    parser.add_argument('--module_out_path', help='', required=True)

    args = parser.parse_args()
    _testcases_dir = os.path.dirname(args.archive_testfile)
    _testsuite_name = os.path.basename(
        args.archive_testfile).replace('.hap', '').replace('module_', '')
    get_hap_json_info(args.project_path, args.build_target_name,
                      args.archive_testfile, args.test_type,
                      args.module_out_path)
    get_hap_module_info(args.build_target_name, _testsuite_name,
                        _testcases_dir, args.subsystem_name,
                        args.part_name, args.project_path)
    copy_hap_case(args.final_hap_path, args.archive_testfile)

    return 0


if __name__ == '__main__':
    sys.exit(main())
