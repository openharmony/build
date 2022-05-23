#!/usr/bin/python3
"""
Copyright (c) 2021 Huawei Device Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import re

class Module():
    def __init__(self, module_name, subsystem_name, part_name, deps, external_deps, raw_data):
        self._module_name = module_name
        self._subsystem_name = subsystem_name
        self._part_name = part_name
        self._deps = deps
        self._external_deps = external_deps
        self._raw_data = raw_data

    @staticmethod
    def create_module_by_string(ohos_string):
        module_name = ''
        subsystem_name = ''
        part_name = ''

        module_pattern = re.compile(r'(?<=ohos_shared_library\(").+(?="\))')
        try:
            module_name = module_pattern.search(ohos_string).group()
        except Exception as e:
            print('The BUILD.gn file is not written in a standard format and cannot be parsed, The error snippet is :')
            print(ohos_string)

        subsystem_pattern = re.compile(r'(?<=subsystem_name = ").+?(?="\n)')
        if subsystem_pattern.search(ohos_string) != None:
            subsystem_name = subsystem_pattern.search(ohos_string).group()
                         
        part_pattern = re.compile(r'(?<=part_name = ").+?(?="\n)')
        if part_pattern.search(ohos_string) != None:
            part_name = part_pattern.search(ohos_string).group()
        
        deps_pattern = re.compile(r'(?<=deps = \[).+?(?=])', re.DOTALL)
        deps_raw = deps_pattern.search(ohos_string).group() if deps_pattern.search(ohos_string) != None \
                   else ''
        deps_list = []
        deps_raw_list = deps_raw.replace('\n','').replace(' ','').replace('"','').split(',')
        for dep in deps_raw_list:
            dep = dep.split('/')[-1]
            deps_list.append(dep)

        external_deps_pattern = re.compile(r'(?<=external_deps = \[).+?(?=])', re.DOTALL)
        external_deps_raw = external_deps_pattern.search(ohos_string).group() if external_deps_pattern.search(ohos_string) != None \
                            else ''
        external_deps_list = []
        external_deps_raw_list = external_deps_raw.replace('\n','').replace(' ','').replace('"','').split(',')
        for dep in external_deps_raw_list:
            dep = dep.split('/')[-1]
            external_deps_list.append(dep)
        
        if external_deps_list.__contains__(''):
            external_deps_list.remove('')
        if deps_list.__contains__(''):
            deps_list.remove('')
        external_deps = set(external_deps_list)
        deps = set(set(deps_list)-external_deps)
        return Module(module_name, subsystem_name, part_name, deps, external_deps, ohos_string)


class Node():
    def __init__(self, component_name):
        self._components_name = component_name
        self._modules = {}
        self._deps = set()
        self._external_deps = set()

    def add_module(self, module):
        self._modules[module._module_name] = module
        self._deps = self._deps | module._deps
        self._external_deps = self._external_deps | module._external_deps

