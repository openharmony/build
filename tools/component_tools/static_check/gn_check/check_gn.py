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
import sys

import pandas as pd
from bundle_check.get_subsystem_with_component import \
    get_subsystem_components_modified
from gn_check.gn_common_tools import GnCommon


class CheckGn(object):
    """GN检查类
    """
    COLUMNS_NAME_FOR_PART = ['文件', '定位', '违反规则', '错误说明']
    COLUMNS_NAME_FOR_ALL = ['子系统', '部件', '文件', '定位', '违反规则', '错误说明']
    SCRIPT_PATH = 'build/tools/component_tools/static_check/gn_check'
    TARGET_NAME = ('ohos_shared_library',
                   'ohos_static_library', 'ohos_executable_library',
                   'ohos_source_set',
                   'ohos_copy',
                   'ohos_group',
                   'ohos_prebuilt_executable',
                   'ohos_prebuilt_shared_library',
                   'ohos_prebuilt_static_library',
                   'ohos_prebuilt_etc')

    def __init__(self, ohos_root: str, black_dir: tuple = tuple(), check_path='') -> None:
        """GN检查类的初始化，定义常用变量及初始化

        Args:
            ohos_root (str): ohos源码的路径，可以是绝对路径，也可以是相对路径
            black_dir (tuple): 不检查的目录
        """

        self.ohos_root = ohos_root
        self.check_path = check_path
        self.black_dir = black_dir

        if check_path == '' or check_path is None:
            self.abs_check_path = self.ohos_root
        else:
            self.abs_check_path = os.path.join(self.ohos_root, check_path)
        self.all_gn_files = GnCommon.find_files(
            self.abs_check_path, black_dirs=black_dir)
        self.subsystem_info = get_subsystem_components_modified(ohos_root)

    def get_all_gn_data(self) -> dict:
        """获取BUILD.gn中所有的target代码段，并返回一个字典

        Returns:
            dict: key是文件名（包含路径），values是target列表
        """

        target_pattern = r"^( *)("
        for target in self.TARGET_NAME:
            target_pattern += target
            if target != self.TARGET_NAME[-1]:
                target_pattern += r'|'
        target_pattern += r")[\s|\S]*?\n\1}$"
        all_gn_data = dict()

        for gn_file in self.all_gn_files:
            if not gn_file.endswith('.gn'):
                continue
            file = open(gn_file, errors='ignore')
            targets_ret = GnCommon.find_paragraph_iter(target_pattern, file.read())
            file.close()
            target = list()  # 每个文件中的target
            for target_ret in targets_ret:
                target.append(target_ret.group())
            if len(target) == 0:
                continue
            all_gn_data.update({gn_file[len(self.ohos_root) + 1:]: target})
        return all_gn_data

    def get_all_abs_path(self) -> list:
        """通过正则表达式匹配出所有BUILD.gn中的绝对路径，并返回一个列表

        Returns:
            list: list中的元素是字典，每个字典中是一条绝对路径的信息
        """
        abs_path_pattern = r'"\/(\/[^\/\n]*){1,63}"'
        ret_list = list()

        all_info = GnCommon.grep_one(
            abs_path_pattern, self.abs_check_path, excludes=self.black_dir, grep_parameter='Porn')
        if all_info is None:
            return list()
        row_info = all_info.split('\n')
        for item in row_info:
            abs_info = item.split(':')
            path = abs_info[0][len(self.ohos_root) + 1:]
            line_number = abs_info[1]
            content = abs_info[2].strip('"')
            ret_list.append(
                {'path': path, 'line_number': line_number, 'content': content})
        return ret_list

    def check_have_product_name(self) -> pd.DataFrame:
        """检查BUILD.gn中是否存product_name和device_name
        返回包含这两个字段的dataframe信息

        不包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '文件', '定位', '违反规则', '错误说明']
        """
        pattern = 'product_name|device_name'
        issue = '存在 product_name 或 device_name'
        rules = '规则4.1 部件编译脚本中禁止使用产品名称变量'
        bad_targets_to_excel = list()
        all_info = GnCommon.grep_one(
            pattern, self.abs_check_path, excludes=self.black_dir)
        if all_info is None:
            return pd.DataFrame()
        product_name_data = all_info.split('\n')
        for line in product_name_data:
            info = line.split(':')
            file_name = info[0][len(self.abs_check_path) + 1:]
            bad_targets_to_excel.append([file_name, 'line:{}:{}'.format(
                info[1], info[2].strip()), rules, issue])
        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_PART)

        return bad_targets_to_excel

    def check_have_product_name_all(self) -> pd.DataFrame:
        """检查BUILD.gn中是否存product_name和device_name
        返回包含这两个字段的dataframe信息

        包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '子系统', '部件', '文件', '定位', '违反规则', '错误说明']
        """
        pattern = 'product_name|device_name'
        issue = '存在 product_name 或 device_name'
        rules = '规则4.1 部件编译脚本中禁止使用产品名称变量'
        bad_targets_to_excel = list()
        all_info = GnCommon.grep_one(
            pattern, self.abs_check_path, excludes=self.black_dir)
        if all_info is None:
            return pd.DataFrame()
        product_name_data = all_info.split('\n')

        for line in product_name_data:
            info = line.split(':')
            file_name = info[0][len(self.ohos_root) + 1:]

            subsys_comp = list()
            for path, content in self.subsystem_info.items():
                if file_name.startswith(path):
                    subsys_comp.append(content['subsystem'])
                    subsys_comp.append(content['component'])
                    break
            if subsys_comp:
                bad_targets_to_excel.append([subsys_comp[0], subsys_comp[1], file_name, 'line:{}:{}'.format(
                    info[1], info[2].strip()), rules, issue])
            else:
                bad_targets_to_excel.append(['null', 'null', file_name, 'line:{}:{}'.format(
                    info[1], info[2].strip()), rules, issue])
        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_ALL)

        return bad_targets_to_excel

    def check_pn_sn(self) -> pd.DataFrame:
        """检查BUILD.gn中target是否包含subsystem_name和part_name字段，
        返回不包含这两个字段的dataframe信息

        不包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '文件', '定位', '违反规则', '错误说明']
        """
        rules = '规则3.2 部件编译目标必须指定部件和子系统名'
        bad_targets_to_excel = list()
        all_gn_data = self.get_all_gn_data()

        for key, values in all_gn_data.items():
            bad_target_to_excel = list()
            if len(values) == 0:
                continue
            for target in values:
                flags = [False, False]
                if target.find('subsystem_name') == -1:
                    flags[0] = True
                if target.find('part_name') == -1:
                    flags[1] = True
                if any(flags):
                    content = target.split()[0]
                    grep_info = GnCommon.grep_one(content, os.path.join(
                        self.ohos_root, key), grep_parameter='n')
                    row_number_info = grep_info.split(':')[0]
                    issue = '不存在 '
                    issue += 'subsystem_name' if flags[0] else ''
                    issue += ',' if all(flags) else ''
                    issue += 'part_name' if flags[1] else ''
                    pos = 'line {}:{}'.format(row_number_info, content)
                    bad_target_to_excel.append(
                        [key[len(self.check_path) + 1:], pos, rules, issue])
            if not bad_target_to_excel:
                continue
            for target_item in bad_target_to_excel:
                bad_targets_to_excel.append(target_item)

        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_PART)

        return bad_targets_to_excel

    def check_pn_sn_all(self) -> pd.DataFrame:
        """检查BUILD.gn中target是否包含subsystem_name和part_name字段，
        返回不包含这两个字段的dataframe信息

        包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '子系统', '部件', '文件', '定位', '违反规则', '错误说明']
        """
        rules = '规则3.2 部件编译目标必须指定部件和子系统名'
        bad_targets_to_excel = list()
        all_gn_data = self.get_all_gn_data()

        for key, values in all_gn_data.items():
            bad_target_to_excel = list()
            if len(values) == 0:
                continue
            for target in values:
                flags = [False, False]
                if target.find('subsystem_name') == -1:
                    flags[0] = True
                if target.find('part_name') == -1:
                    flags[1] = True
                if any(flags):
                    content = target.split('\n')[0].strip()
                    grep_info = GnCommon.grep_one(content, os.path.join(
                        self.ohos_root, key), grep_parameter='n')
                    row_number_info = grep_info.split(':')[0]
                    issue = '不存在 '
                    issue += 'subsystem_name' if flags[0] else ''
                    issue += ',' if all(flags) else ''
                    issue += 'part_name' if flags[1] else ''
                    pos = 'line {}:{}'.format(row_number_info, content)
                    bad_target_to_excel.append(
                        ['null', 'null', key, pos, rules, issue])
            if not bad_target_to_excel:
                continue
            for path, content in self.subsystem_info.items():
                if key.startswith(path):
                    bad_target_to_excel[:][:2] = content['subsystem'], content['component']
                    
            for target_item in bad_target_to_excel:
                bad_targets_to_excel.append(target_item)

        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_ALL)

        return bad_targets_to_excel

    def check_abs_path(self) -> pd.DataFrame:
        """检查绝对路径，返回标准信息

        不包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '文件', '定位', '违反规则', '错误说明']
        """
        rules = '规则3.1 部件编译脚本中只允许引用本部件路径，禁止引用其他部件的绝对或相对路径'
        issue = '引用使用了绝对路径'
        bad_targets_to_excel = list()
        abs_path = self.get_all_abs_path()

        for item in abs_path:
            if item['content'].startswith('//third_party') \
                    or item['content'].startswith('//build'):
                continue
            bad_targets_to_excel.append([item['path'][len(
                self.check_path) + 1:], 'line {}:{}'.format(item['line_number'], item['content']), rules, issue])
        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_PART)

        return bad_targets_to_excel

    def check_abs_path_all(self) -> pd.DataFrame:
        """检查绝对路径，返回标准信息

        包含子系统部件信息版本

        Returns:
            pd.DataFrame: 数据的组织方式为[
            '子系统', '部件', '文件', '定位', '违反规则', '错误说明']
        """
        rules = '规则3.1 部件编译脚本中只允许引用本部件路径，禁止引用其他部件的绝对或相对路径'
        issue = '引用使用了绝对路径'
        bad_targets_to_excel = list()
        abs_path = self.get_all_abs_path()

        for item in abs_path:
            if item['content'].startswith('//third_party') \
                    or item['content'].startswith('//build'):
                continue
            subsys_comp = list()
            for path, content in self.subsystem_info.items():
                if item['path'].startswith(path):
                    subsys_comp.append(content['subsystem'])
                    subsys_comp.append(content['component'])
                    break
            if subsys_comp:
                bad_targets_to_excel.append([subsys_comp[0], subsys_comp[1], item['path'], 'line {}:{}'.format(
                    item['line_number'], item['content']), rules, issue])
            else:
                bad_targets_to_excel.append(['null', 'null', item['path'], 'line {}:{}'.format(
                    item['line_number'], item['content']), rules, issue])
        bad_targets_to_excel = pd.DataFrame(
            bad_targets_to_excel, columns=self.COLUMNS_NAME_FOR_ALL)

        return bad_targets_to_excel

    def output(self):
        if self.check_path == '' or self.check_path is None:
            product_name_info = self.check_have_product_name_all()
            part_name_subsystem_name_info = self.check_pn_sn_all()
            abs_path_info = self.check_abs_path_all()
        else:
            product_name_info = self.check_have_product_name()
            part_name_subsystem_name_info = self.check_pn_sn()
            abs_path_info = self.check_abs_path()

        out = pd.concat(
            [product_name_info, part_name_subsystem_name_info, abs_path_info])

        print('-------------------------------')
        print('BUILD.gn check successfully!')
        print('There are {} issues in total'.format(out.shape[0]))
        print('-------------------------------')

        return out
