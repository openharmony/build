#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
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
import re
import glob
import os.path
import stat


class Analyzer:
    @classmethod
    def get_components_from_inherit_attr(cls, components, inherit, project):
        for json_name in inherit:
            with open(project + os.sep + json_name, 'r', encoding='utf-8') as r:
                inherit_file = json.load(r)
            for subsystem in inherit_file['subsystems']:
                for component in subsystem['components']:
                    component['subsystem'] = subsystem['subsystem']
                    components.append(component)

    @classmethod
    def check(cls, include):
        if include is not None and './' in include.group():
            return True
        return False

    @classmethod
    def scan_files(cls, components, proj_path):
        results = []
        for component in components:
            if not component.__contains__('scan_path') or component['scan_path'].strip() == '':
                continue
            files = glob.glob(os.path.join(component['scan_path'], '**', '*.c'), recursive=True)
            files.extend(glob.glob(os.path.join(component['scan_path'], '**', '*.cpp'), recursive=True))
            files.extend(glob.glob(os.path.join(component['scan_path'], '**', '*.cc'), recursive=True))
            files.extend(glob.glob(os.path.join(component['scan_path'], '**', '*.h'), recursive=True))
            for file in files:
                try:
                    cls.scan_each_file(component, file, proj_path, results)
                except UnicodeDecodeError as e:
                    print("scan file {} with unicode decode error: {}".format(file, e))
        return results

    @classmethod
    def scan_each_file(cls, component, file, project_path, results):
        with open(file, 'r', encoding='ISO-8859-1') as f:
            line_list = f.readlines()
            line_num = 0
            for line in line_list:
                include = re.match(r'#include\s+"([^">]+)"', line)
                line_num = line_num + 1
                if cls.check(include):
                    result = {'line_num': line_num, 'file_path': file.replace(project_path, "/"),
                              'include_cmd': include.group(), 'component': component['component'],
                              'subsystem': component['subsystem']}
                    results.append(result)

    @classmethod
    def analysis(cls, config: str, project_path: str, components_info: str, output_path: str):
        if not os.path.exists(config):
            print("error: {} is inaccessible or not found".format(config))
            return
        if not os.path.exists(project_path):
            print("error: {} is inaccessible or not found".format(project_path))
            return
        if not os.path.exists(components_info):
            print("error: {} is inaccessible or not found".format(components_info))
            return
        components = cls.__get_components(config, project_path)
        cls.__get_need_scan_path(components, project_path, components_info)
        print("scan:")
        print([item['scan_path'] for item in components], project_path)
        result = cls.scan_files(components, project_path)
        flags = os.O_WRONLY | os.O_CREAT
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(output_path, flags, modes), 'w') as f:
            for ele in result:
                items = ele['subsystem'], ele['component'], ele['file_path'], str(ele['line_num']), ele['include_cmd']
                f.write(" ".join(items) + "\n")

    @classmethod
    def __get_need_scan_path(cls, components, project, components_info_path):
        path_info = dict()
        with open(components_info_path, 'r', encoding='utf-8') as r:
            xml_info = r.readlines()
        for line in xml_info:
            if "path=" in line:
                path = re.findall('path="(.*?)"', line)[0]
                component = path.split('/')[-1]
                path_info[component] = path
        item_list = list(path_info.keys())
        for component in components:
            if component['component'] in path_info.keys():
                component['scan_path'] = project + '/' + path_info[component['component']]
                if (component['component'] in item_list):
                    item_list.remove(component['component'])
            else:
                component['scan_path'] = ''
        print("no scan component :" + " ".join(item_list))

    @classmethod
    def __get_components(cls, config: str, project: str):
        components = list()
        with open(config, 'r', encoding='utf-8') as r:
            config_json = json.load(r)
        if "inherit" in config_json.keys():
            inherit = config_json['inherit']
            cls.get_components_from_inherit_attr(components, inherit, project)
        for subsystem in config_json['subsystems']:
            for component in subsystem['components']:
                if component not in components:
                    component['subsystem'] = subsystem['subsystem']
                    components.append(component)
        return components



def get_args():
    parser = argparse.ArgumentParser(
        description=f"common_template.\n")
    parser.add_argument("-c", "--config_path", required=True, type=str,
                        help="path of config_file", default="")
    parser.add_argument("-p", "--project_path", type=str, required=False,
                        help="root path of openharmony. eg: -p ~/openharmony", default="./")
    parser.add_argument("-x", "--xml_path", type=str, required=True,
                        help="path of ohos.xml", default="")
    parser.add_argument("-o", "--output_path", required=False, type=str,
        default="include_relative_path.list", help="name of output_json")
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    local_config_path = args.config_path
    local_project_path = args.project_path
    local_xml_path = args.xml_path
    local_output_path = args.output_path
    Analyzer.analysis(local_config_path, local_project_path, local_xml_path, local_output_path)
