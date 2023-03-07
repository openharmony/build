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

import shutil
import os
import sys
import argparse

"""Add part replace test case

Usage: test_set.py --add
Add part repalce test case, and set build env.

Usage: test_set.py --reset
Remove part replace test case from oh build environment.
"""


def find_top():
    cur_dir = os.getcwd()
    while cur_dir != "/":
        build_scripts = os.path.join(
            cur_dir, 'build/config/BUILDCONFIG.gn')
        if os.path.exists(build_scripts):
            return cur_dir
        cur_dir = os.path.dirname(cur_dir)


top_dir = find_top()

product_config_json = "config.json"
origin_component = "origin_component"
component_a = "component_a"
subsystem_config_json = "subsystem_config.json"
subsystem_components_whitelist_json = "subsystem_compoents_whitelist.json"
testpart = "testpart"

product_dest_path = os.path.join(top_dir, "vendor/hihope/rk3568/config.json")
subsystem_config_path = os.path.join(top_dir, "build/subsystem_config.json")
subsystem_components_whitelist_path = os.path.join(top_dir, "build/subsystem_compoents_whitelist.json")
testpart_dest_path = os.path.join(top_dir, "vendor/testpart")
origin_component_path = os.path.join(
    top_dir, "foundation/arkui/origin_component")
component_a_path = os.path.join(top_dir, "foundation/arkui/component_a")


def add_test_case():
    if os.path.exists("{}.backup".format(product_dest_path)):
        raise Exception(
            "you have modified the product's config.json, please use --reset to initialize oh env first!")
    if os.path.exists("{}.backup".format(subsystem_config_path)):
        raise Exception(
            "you have modified the subsystem_config.json, please use --reset to initialize oh env first!")

    if os.path.exists("{}.backup".format(subsystem_components_whitelist_path)):
        raise Exception(
            "you have modified the subsystem_compoents_whitelist.json, please use --reset to initialize oh env first!")

    shutil.move(product_dest_path, "{}.backup".format(product_dest_path))
    shutil.move(subsystem_config_path,
                "{}.backup".format(subsystem_config_path))
    shutil.move(subsystem_components_whitelist_path,
                "{}.backup".format(subsystem_components_whitelist_path))

    shutil.copy(product_config_json, product_dest_path)
    shutil.copy(subsystem_config_json, subsystem_config_path)
    shutil.copy(subsystem_components_whitelist_json, subsystem_components_whitelist_path)

    shutil.copytree(testpart, testpart_dest_path,
                    symlinks=False, ignore=None)
    shutil.copytree(origin_component, origin_component_path,
                    symlinks=False, ignore=None)
    shutil.copytree(component_a, component_a_path,
                    symlinks=False, ignore=None)


def reset_env():
    if os.path.exists("{}.backup".format(product_dest_path)):
        shutil.move("{}.backup".format(product_dest_path), product_dest_path)

    if os.path.exists("{}.backup".format(subsystem_config_path)):
        shutil.move("{}.backup".format(
            subsystem_config_path), subsystem_config_path)

    if os.path.exists("{}.backup".format(subsystem_components_whitelist_path)):
        shutil.move("{}.backup".format(
            subsystem_components_whitelist_path), subsystem_components_whitelist_path)

    if os.path.exists(testpart_dest_path):
        shutil.rmtree(testpart_dest_path)

    if os.path.exists(origin_component_path):
        shutil.rmtree(origin_component_path)

    if os.path.exists(component_a_path):
        shutil.rmtree(component_a_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', action='store_true', help="add test case")
    parser.add_argument('--reset', action='store_true',
                        help="remove added test case, reset oh env")
    args = parser.parse_args()

    if args.add and args.reset:
        return -1
    if args.add:
        add_test_case()
    if args.reset:
        reset_env()
    return 0


if __name__ == '__main__':
    sys.exit(main())
