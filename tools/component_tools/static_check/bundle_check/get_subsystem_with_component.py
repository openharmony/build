#!/usr/bin/env python3
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
import os
import stat
import json
from lite.hb_internal.common.config import Config


class ErrorInfo:
    g_subsystem_path_error = []  # subsystem path exist in subsystem_config.json
    g_component_path_empty = []  # bundle.json path which cant get component path.
    g_component_abs_path = []    # destPath can't be absolute path.


def get_subsystem_components(ohos_path: str):
    subsystem_json_path = os.path.join(
        ohos_path, r"build/subsystem_config.json")
    subsystem_item = {}

    with open(subsystem_json_path, 'rb') as file:
        subsystem_json = json.load(file)

    conf = Config()
    subsystem_json_overlay_path =  conf.product_path + '/subsystem_config_overlay.json'
    if os.path.isfile(subsystem_json_overlay_path):
        with open(subsystem_json_overlay_path, 'rb') as file:
            subsystem_overlay_json = json.load(file)
            subsystem_json.update(subsystem_overlay_json)

    bundle_json_list = []
    subsystem_name = ""
    # get sunsystems
    for i in subsystem_json:
        subsystem_name = subsystem_json[i]["name"]
        subsystem_path = os.path.join(ohos_path, subsystem_json[i]["path"])
        if not os.path.exists(subsystem_path):
            ErrorInfo.g_subsystem_path_error.append(subsystem_path)
            continue
        cmd = 'find %s -name bundle.json' % subsystem_path
        bundle_json_list = os.popen(cmd).readlines()

        # get components
        component_list = []
        for j in bundle_json_list:
            bundle_path = j.strip()
            with open(bundle_path, 'rb') as bundle_file:
                bundle_json = json.load(bundle_file)
            component_item = {}
            if 'segment' in bundle_json and 'destPath' in bundle_json["segment"]:
                destpath = bundle_json["segment"]["destPath"]
                component_item[bundle_json["component"]["name"]] = destpath
                if os.path.isabs(destpath):
                    ErrorInfo.g_component_abs_path.append(destpath)
            else:
                component_item[bundle_json["component"]["name"]] = \
                                "Unknow. Please check %s" % bundle_path
                ErrorInfo.g_component_path_empty.append(bundle_path)
            component_list.append(component_item)

        subsystem_item[subsystem_name] = component_list
    return subsystem_item


def get_subsystem_components_modified(ohos_root) -> dict:
    ret = dict()

    subsystem_info = get_subsystem_components(ohos_root)
    if subsystem_info is None:
        return ret
    for subsystem_k, subsystem_v in subsystem_info.items():
        for component in subsystem_v:
            for key, value in component.items():
                ret.update({value: {'subsystem': subsystem_k, 'component': key}})
    return ret


def export_to_json(subsystem_item: dict,
                   output_path: str,
                   output_name: str = "subsystem_component_path.json"):
    subsystem_item_json = json.dumps(
        subsystem_item, indent=4, separators=(', ', ': '))

    out_abs_path = os.path.abspath(
        os.path.normpath(output_path)) + '/' + output_name
    flags = os.O_WRONLY | os.O_CREAT
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(out_abs_path, flags, modes), 'w') as file:
        file.write(subsystem_item_json)
    print("output path: " + out_abs_path)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="project root path.", type=str)
    parser.add_argument("-o", "--outpath",
                        help="specify an output path.", type=str)
    args = parser.parse_args()

    ohos_path = os.path.abspath(args.project)
    if not is_project(ohos_path):
        print("'" + ohos_path + "' is not a valid project path.")
        exit(1)

    output_path = r'.'
    if args.outpath:
        output_path = args.outpath

    return ohos_path, output_path


def is_project(path: str) -> bool:
    '''
    @func: 判断是否源码工程。
    @note: 通过是否含有 .repo/manifests 目录粗略判断。
    '''
    norm_parh = os.path.normpath(path)
    return os.path.exists(norm_parh + '/.repo/manifests')


def print_warning_info():
    '''
    @func: 打印一些异常信息。
    '''
    def print_list(print_list):
        for i in print_list:
            print('\t' + i)

    if ErrorInfo.g_component_path_empty or \
        ErrorInfo.g_component_abs_path:
        print("------------ warning info ------------------")

    if ErrorInfo.g_subsystem_path_error:
        print("subsystem path not exist:")
        print_list(ErrorInfo.g_subsystem_path_error)

    if ErrorInfo.g_component_path_empty:
        print("can't find destPath in:")
        print_list(ErrorInfo.g_component_path_empty)

    if ErrorInfo.g_component_abs_path:
        print("destPath can't be absolute path:")
        print_list(ErrorInfo.g_component_abs_path)


if __name__ == '__main__':
    oh_path, out_path = parse_args()
    info = get_subsystem_components(oh_path)
    export_to_json(info, out_path)
    print_warning_info()
