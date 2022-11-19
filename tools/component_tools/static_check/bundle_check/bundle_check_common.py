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

import os
import re


class BundleCheckTools:
    '''用于检查 bundle.json 的工具箱。'''

    @staticmethod
    def is_all_lower(string:str):
        ''' 判断字符串是否有且仅有小写字母。'''
        if not string:
            return False
        for i in string:
            if not (97 <= ord(i) <= 122):
                return False
        return True

    @staticmethod
    def is_number(string:str) -> bool:
        ''' 判断字符串 s 是否能表示为数值。'''
        try:
            float(string)
            return True
        except (OverflowError, ValueError):
            return False

    @staticmethod
    def split_by_unit(string:str):
        '''分离 s 字符串的数值和单位'''
        match = re.match(r'^[~]?(\d+)([a-zA-Z]*)$', string)
        if not match:
            return (0, '')
        return (float(match.group(1)), match.group(2))

    @staticmethod
    def get_root_path() -> str:
        cur_path = os.path.dirname(os.path.abspath(__file__))
        root_path = os.path.normpath(os.path.join(cur_path, '../../../../../'))
        try:
            if BundleCheckTools.is_project(root_path):
                return root_path
            else:
                raise ValueError(
                    'get root path failed, please check script "bundle_check_common.py" under '
                    'the path(build/tools/component_tools/static_check/bundle_check).')
        except ValueError as get_path_error:
            print("Error: ", repr(get_path_error))
        return ""

    @staticmethod
    def is_project(path:str) -> bool:
        '''
        @func: 判断路径是否源码工程。
        @note: 通过是否存在 .repo/manifests 目录判断。
        '''
        if not path:
            return False
        abs_path = os.path.abspath(os.path.normpath(path))
        return os.path.exists(abs_path + '/' + '.repo/manifests')

    @staticmethod
    def get_ohos_version(root:str) -> str:
        if not BundleCheckTools.is_project(root):
            return ""

        version_path = os.path.join(root, 'build/version.gni')
        lines = []
        with open(version_path, 'r', encoding='utf-8') as version_file:
            lines = version_file.readlines()
        for line in lines:
            line = line.strip()
            if line and line[0] == '#':
                continue
            if 'sdk_version =' in line:
                match_result = re.match(r'\s*sdk_version\s*=\s*"(\d+\.\d+).*"', line)
                if match_result:
                    return match_result.group(1)
                else:
                    return ""
        return ""