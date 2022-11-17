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

import os
import sys
import json
import argparse
import re

CHECK_RULE_2_1 = r"规则2.1 部件描述文件中字段须准确。"

NAME_NO_FIELD = r'缺少 "name" 字段。'
NAME_EMPTY = r'"name" 字段不能为空。'
NAME_FORMAT_ERROR = r"格式错误, 命名规则为: @{organization}/{component_name}。"
NAME_LOWCASE = r'"name" 字段的英文字符均为小写。'
COMPONENT_NAME_FROMAT = r"部件名使用小写加下划线风格命名, 如: unix_like。"
COMPONENT_NAME_FROMAT_LEN = r"部件名不能超过 63 个有效英文字符."

VERSION_NO_FIELD = r'缺少 "version" 字段。'
VERSION_ERROR = r'"version" 值有误，请检查。'

SEGMENT_NO_FIELD = r'缺少 "segment" 字段。'
SEGMENT_DESTPATH_NO_FIELD = r'缺少 "segment:destPath" 字段。'
SEGMENT_DESTPATH_EMPTY = r'"segment:destPath" 字段不能为空。'
SEGMENT_DESTPATH_UNIQUE = r'"segment:destPath" 只能有一个路径。'
SEGMENT_DESTPATH_ABS = r'"segment:destPath" 只能为相对路径。'

COMPONENT_NO_FIELD = r'缺少 "component" 字段。'
COMPONENT_NAME_NO_FIELD = r'缺少 "component:name" 字段。'
COMPONENT_NAME_EMPTY = r'"component:name" 字段不能为空。'
COMPONENT_NAME_VERACITY = r'"component:name" 字段应该与 "name" 字段部件名部分相同。'
COMPONENT_SUBSYSTEM_NO_FIELD = r'缺少 "component:subsystem" 字段。'
COMPONENT_SUBSYSTEM_EMPTY = r'"component:subsystem" 字段不能为空。'
COMPONENT_SUBSYSTEM_LOWCASE = r'"component:subsystem" 值必须为全小写字母。'
COMPONENT_SYSCAP_STRING_EMPTY = r'"component:syscap" 中的值不能为空字符串。'
COMPONENT_SYSCAP_HEADER_ERROR = r'"component:syscap" 中的值必须以 "SystemCapability." 开头。'
COMPONENT_SYSCAP_STRING_STYLE = r'"component:syscap" 中的值必须为大驼峰命名规则。'
COMPONENT_SYSCAP_STRING_FORMAT_ERROR = r'"component:syscap" 中的值命名规则为 "SystemCapability.子系统.部件能力.子能力（可选）"。\
    如, SystemCapability.Media>Camera, SystemCapability.Media.Camera.Front。'
COMPONENT_FEATURES_STRING_EMPTY = r'"component:features" 中的值不能为空字符串。'
COMPONENT_FEATURES_SEPARATOR_ERROR = r'"component:features" 的值须加上部件名为前缀并以 "_" 为分隔符"。'
COMPONENT_AST_NO_FIELD = r'缺少 "component:adapted_system_type" 字段。'
COMPONENT_AST_EMPTY = r'"component:adapted_system_type" 字段不能为空。'
COMPONENT_AST_NO_REP = r'"component:adapted_system_type" 值最多只能有 3 个（"mini", "small", "standard"）且不能重复。'
COMPONENT_ROM_NO_FIELD = r'缺少 "component:rom" 字段。'
COMPONENT_ROM_EMPTY = r'"component:rom" 字段不能为空。'
COMPONENT_ROM_SIZE_ERROR = r'"component:rom" 非数值或者小于等于0。'
COMPONENT_ROM_UNIT_ERROR = r'"component:rom" 的单位错误(KB, KByte, MByte, MB, 默认为KByte)'
COMPONENT_RAM_NO_FIELD = r'缺少 "component:ram" 字段。'
COMPONENT_RAM_EMPTY = r'"component:ram" 字段不能为空。'
COMPONENT_RAM_SIZE_ERROR = r'"component:ram" 非数值或者小于等于0。'
COMPONENT_RAM_UNIT_ERROR = r'"component:ram" 的单位错误(KB, KByte, MByte, MB, 默认为KByte)'
COMPONENT_DEPS_NO_FIELD = r'缺少 "component:deps" 字段。'

class BundleCheckTools:
    '''用于检查 bundle.json 的工具箱。'''

    @staticmethod
    def is_number(s:str) -> bool:
        '''
        @func: 判断字符串 s 是否能表示为数值。
        '''
        try:
            float(s)
            return True
        except (OverflowError, ValueError):
            return False

    @staticmethod
    def split_by_unit(s:str):
        '''
        @func: 分离 s 字符串的数值和单位
        '''
        if s[0] == '~': # 去除 ram 前面的 '~' 字符
            s = s[1:]
        if BundleCheckTools.is_number(s):
            return float(s), ''
        for n, u in enumerate(s):
            if not (u.isdigit() or u == '.' or u == '-'):
                break
        try:
            num = float(s[:n])
        except ValueError as e:
            num = 0
        unit = s[n:]
        return num, unit

    @staticmethod
    def get_root_path() -> str:
        cur_path = os.path.dirname(os.path.abspath(__file__))
        root_path = os.path.normpath(os.path.join(cur_path, '../../../../../'))
        print('mmmm', cur_path, root_path)
        if BundleCheckTools.is_project(root_path):
            return root_path
        return None

    @staticmethod
    def is_project(path:str) -> bool:
        '''
        @func: 判断路径是否源码工程。
        @note: 通过是否存在 .repo/manifests 目录判断。
        '''
        p = os.path.abspath(os.path.normpath(path))
        return os.path.exists(p + '/' + '.repo/manifests')

    @staticmethod
    def get_ohos_version(root_path:str) -> str:
        root = os.path.abspath(root_path)
        if not BundleCheckTools.is_project(root):
            return None
        version_path = os.path.join(root, 'build/version.gni')
        with open(version_path, 'r', encoding='utf-8') as version_file:
            for line in version_file.readlines():
                line = line.strip()
                if line and line[0] == '#':
                    continue
                if 'sdk_version =' in line:
                    match_result = re.match(r'\s*sdk_version\s*=\s*"(\d+\.\d+)\.*"', line)
                    if match_result:
                        return match_result.group(1)
                    else:
                        return None

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
        d = {}
        for file_path in  diff:
            d[file_path] = []
            diff_list = diff[file_path]
            for i in diff_list:
                ret = BundleCheckTools._check_diff_by_line(i[1])
                if ret:
                    line = list(("line" + str(i[0]) + ": " + i[1], ret))
                    d[file_path].append(line)
        # trans to list
        l = []
        for f in d:
            for i in d[f]:
                row = [f, CHECK_RULE_2_1]
                row.extend([i[0], i[1]])
                l.append(row)
        if l:
            return True, l
        else:
            return False, l

    def _check_diff_by_line(s:str) -> str:
        s = s.strip()
        match = re.match(r'"(\w+)":\s*"(.*)"', s)
        if not match:
            return None
        key = match.group(1)
        value = match.group(2)
        if key == 'name':
            if value.startswith('//') and ':' in value:
                # exclude inner_kits:name
                return None
            v = value.split('/')[1] if ('/' in value) else value
            if not (0 < len(v) < 64):
                return COMPONENT_NAME_FROMAT_LEN
            if not re.match(r'([a-z]+_)*([a-z]+)\b', v):
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
        return None
