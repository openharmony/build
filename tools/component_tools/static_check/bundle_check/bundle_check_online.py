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
from bundle_check.warning_info import BCWarnInfo


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
                if not ret:
                    continue
                line = list(("line" + str(i[0]) + ": " + i[1], ret))
                if file_path in diff_dict.keys():
                    diff_dict[file_path].append(line)
        # trans to list
        err_list = []
        for file in diff_dict:
            for i in diff_dict[file]:
                row = [file, i[0]]
                row.extend([BCWarnInfo.CHECK_RULE_2_1, i[1]])
                err_list.append(row)
        if err_list:
            return True, err_list
        else:
            return False, err_list

    def check_diff_by_line(line:str) -> str:
        line = line.strip()
        match = re.match(r'"(\w+)"\s*:\s*"(.*)"', line)
        if not match:
            return ""
        key = match.group(1)
        value = match.group(2)
        
        if key == 'name':
            return _check_line_name(value)
        if key == 'version':
            return _check_line_version(value)
        if key == 'destPath':
            if os.path.isabs(value):
                return BCWarnInfo.SEGMENT_DESTPATH_ABS
            return ""
        if key == 'subsystem':
            if not re.match(r'[a-z]+$', value):
                return BCWarnInfo.COMPONENT_SUBSYSTEM_LOWCASE
        if key == 'rom' or key == 'ram':
            return _check_line_rom_ram(key, value)
        if key == 'syscap':
            return _check_line_syscap(value)
        if key == 'features':
            if len(value) == 0:
                return BCWarnInfo.COMPONENT_FEATURES_STRING_EMPTY
        return ""


def _check_line_name(value):
    if not value: # value empty
        return BCWarnInfo.NAME_EMPTY
    if value.startswith('//') and ':' in value: # exclude inner_kits:name
        return ""
    if ('/' in value) and (not BundleCheckTools.match_bundle_full_name(value)):
        return BCWarnInfo.NAME_FORMAT_ERROR + \
            BCWarnInfo.COMPONENT_NAME_FROMAT_LEN

    component_name = value.split('/')[1] if ('/' in value) else value
    if not BundleCheckTools.match_unix_like_name(component_name):
        return BCWarnInfo.COMPONENT_NAME_FROMAT
    return ""


def _check_line_version(value):
    if len(value) < 3:
        return BCWarnInfo.VERSION_ERROR
    ohos_root_path = BundleCheckTools.get_root_path()
    if not ohos_root_path:
        # when project is not exist, do not raise checking error
        return ""
    ohos_version = BundleCheckTools.get_ohos_version(ohos_root_path)
    if ohos_version and value != ohos_version:
        return BCWarnInfo.VERSION_ERROR + ' ohos version is: ' + value
    return ""


def _check_line_rom_ram(key, value):
    if len(value) == 0:
        return r'"component:rom/ram" 字段不能为空。'
    num, unit = BundleCheckTools.split_by_unit(value)
    if num <= 0:
        return '"component:{}" 非数值或者小于等于 0。'.format(key)
    if unit:
        unit_types = ["KB", "KByte", "MByte", "MB"]
        if unit not in unit_types:
            return '"component:{}" 的单位错误（KB, KByte, MByte, MB，默认为KByte）。'.format(key)
    return ""


def _check_line_syscap(value):
    if len(value) == 0:
        return BCWarnInfo.COMPONENT_SYSCAP_STRING_EMPTY
    match = re.match(r'^SystemCapability(\.[A-Z][a-zA-Z]{1,63}){2,6}$', value)
    if not match:
        return BCWarnInfo.COMPONENT_SYSCAP_STRING_FORMAT_ERROR
    return ""