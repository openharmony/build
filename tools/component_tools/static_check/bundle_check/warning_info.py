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

class BCWarnInfo:
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
    COMPONENT_SYSCAP_STRING_FORMAT_ERROR = r'''"component:syscap" 中的值命名规则为 "SystemCapability.子系统.部件能力.子能力（可选）"。
    如, SystemCapability.Media.Camera, SystemCapability.Media.Camera.Front。并且每个部分必须为大驼峰命名规则'''
    COMPONENT_FEATURES_STRING_EMPTY = r'"component:features" 中的值不能为空字符串。'
    COMPONENT_FEATURES_SEPARATOR_ERROR = r'"component:features" 的值须加上部件名为前缀并以 "_" 为分隔符"。'
    COMPONENT_FEATURES_FORMAT_ERROR = r'"component:features" 命名格式为 "{componentName}_feature_{featureName}"。'
    COMPONENT_AST_NO_FIELD = r'缺少 "component:adapted_system_type" 字段。'
    COMPONENT_AST_EMPTY = r'"component:adapted_system_type" 字段不能为空。'
    COMPONENT_AST_NO_REP = r'"component:adapted_system_type" 值最多只能有 3 个（"mini", "small", "standard"）且不能重复。'
    COMPONENT_ROM_NO_FIELD = r'缺少 "component:rom" 字段。'
    COMPONENT_ROM_EMPTY = r'"component:rom" 字段不能为空。'
    COMPONENT_ROM_SIZE_ERROR = r'"component:rom" 非数值或者小于0。'
    COMPONENT_ROM_UNIT_ERROR = r'"component:rom" 的单位错误(KB, KByte, MByte, MB, 默认为KByte)'
    COMPONENT_RAM_NO_FIELD = r'缺少 "component:ram" 字段。'
    COMPONENT_RAM_EMPTY = r'"component:ram" 字段不能为空。'
    COMPONENT_RAM_SIZE_ERROR = r'"component:ram" 非数值或者小于等于0。'
    COMPONENT_RAM_UNIT_ERROR = r'"component:ram" 的单位错误(KB, KByte, MByte, MB, 默认为KByte)'
    COMPONENT_DEPS_NO_FIELD = r'缺少 "component:deps" 字段。'