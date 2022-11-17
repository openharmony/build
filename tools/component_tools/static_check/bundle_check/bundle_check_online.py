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
from bundle_check.bundle_check_common import BundleCheckTools
from bundle_check.warning_info import *


class BundleCheckOnline:
    '''用于检查 bundle.json pr。'''

    @staticmethod
    def check_diff(diff:dict):
        '''
        @func: 根据 diff 部分对 bundle.json 进行静态检查。
        @parm:
            ``diff``: 格式化后的字典类型的 diff 文件修改信息。示例:
                d = {
                    "path1/bundle.json": [
                        [line1, "content1"],
                        [line2, "content2"]
                    ]
                }
        '''
        diff_dict = {}
        for file_path in diff:
            diff_dict[file_path] = []
            diff_list = diff[file_path]
            for i in diff_list:
                ret = BundleCheckOnline.check_diff_by_line(i[1])
                if ret:
                    line = list(("line" + str(i[0]) + ": " + i[1], ret))
                    if file_path in diff_dict.keys():
                        diff_dict[file_path].append(line)
        # trans to list
        err_list = []
        for file in diff_dict:
            for i in diff_dict[file]:
                row = [file, i[0]]
                row.extend([CHECK_RULE_2_1, i[1]])
                err_list.append(row)
        if err_list:
            return True, err_list
        else:
            return False, err_list

    def check_diff_by_line(line:str) -> str:
        line = line.strip()
        match = re.match(r'"(\w+)":\s*"(.*)"', line)
        if not match:
            return None
        key = match.group(1)
        value = match.group(2)
        if key == 'name':
            if value.startswith('//') and ':' in value:
                # exclude inner_kits:name
                return None
            component_name = value.split('/')[1] if ('/' in value) else value
            if not (0 < len(component_name) < 64):
                return COMPONENT_NAME_FROMAT_LEN
            if not re.match(r'([a-z]+_)*([a-z]+)\b', component_name):
                return COMPONENT_NAME_FROMAT
            return None
        if key == 'version':
            if len(value) < 3:
                return VERSION_ERROR
            ohos_root_path = BundleCheckTools.get_root_path()
            if ohos_root_path is None:
                # when project is not exist, do not raise checking error
                return None
            ohos_version = BundleCheckTools.get_ohos_version(ohos_root_path)
            if value != ohos_version:
                return VERSION_ERROR + ' ohos version is: ' + value
            return None
        if key == 'destPath':
            if os.path.isabs(value):
                return SEGMENT_DESTPATH_ABS
            return None
        if key == 'subsystem':
            if not re.match(r'[a-z]+$', value):
                return COMPONENT_SUBSYSTEM_LOWCASE
        if key == 'rom' or key == 'ram':
            if len(value) == 0:
                return r'"component:rom/ram" 字段不能为空。'
            num, unit = BundleCheckTools.split_by_unit(value)
            if num <= 0:
                return '"component:{}" 非数值或者小于等于 0。'.format(key)
            if unit:
                unit_types = ["KB", "KByte", "MByte", "MB"]
                if unit not in unit_types:
                    return '"component:{}" 的单位错误（KB, KByte, MByte, MB，默认为KByte）。'.format(key)
        if key == 'syscap':
            if len(value) == 0:
                return COMPONENT_SYSCAP_STRING_EMPTY
            match = re.match(r'^SystemCapability(\.[A-Z][a-zA-Z]+)+$', value)
            if not match:
                return COMPONENT_SYSCAP_STRING_FORMAT_ERROR
        if key == 'features':
            if len(value) == 0:
                return COMPONENT_FEATURES_STRING_EMPTY
        return None
