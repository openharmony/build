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

import re
import sys
import os


class CheckGnOnline(object):
    TARGET_NAME = ('ohos_shared_library',
                   'ohos_static_library', 'ohos_executable_library',
                   'ohos_source_set',
                   'ohos_copy',
                   'ohos_group',
                   'ohos_prebuilt_executable',
                   'ohos_prebuilt_shared_library',
                   'ohos_prebuilt_static_library',
                   'ohos_prebuilt_etc')

    def __init__(self, gn_data: dict) -> None:
        self.status = True
        self.gn_data = gn_data
        self.err_info = list()
        config_path = os.path.join(
            sys.path[0], 'config/csct_whitelist.conf')
        norm_path = os.path.normpath(config_path)
        with open(norm_path, 'r') as file:
            whitelist = file.read().split('\n')
            self.whitelist = tuple(whitelist)

    def merge_line(self) -> dict:
        ret_dict = dict()
        for key, values in self.gn_data.items():
            contents = ''
            row_range = list()
            start = -2
            end = -2
            for line in values:
                pos = line[0]
                content = line[1]

                if pos == end + 1:
                    end = pos
                    contents += '\n{}'.format(content)
                else:
                    if start != end:
                        row_range.append([start, end, contents])
                    contents = content
                    start = pos
                    end = pos

                if pos == values[-1][0] and start != end:
                    row_range.append([start, end, contents])

            ret_dict.update({key: row_range})
        return ret_dict

    def check_have_product_name(self, key: str, line: list) -> None:
        rules = '规则4.1 部件编译脚本中禁止使用产品名称变量'
        check_list = ['product_name', 'device_name']
        flag = {check_list[0]: False, check_list[1]: False}
        for check_item in check_list:
            if line[1].find(check_item) != -1:
                flag[check_item] = True
        if any(flag.values()):
            issue = '存在'
            issue += check_list[0] if flag[check_list[0]] else ''
            issue += ',' if all(flag.values()) else ''
            issue += check_list[1] if flag[check_list[1]] else ''
            pos = "line:{}  {}".format(line[0], line[1])
            self.err_info.append([key, pos, rules, issue])
            self.status = False
        return

    def check_abs_path(self, key: str, line: list) -> None:
        rules = '规则3.1 部件编译脚本中只允许引用本部件路径，禁止引用其他部件的绝对或相对路径'
        issue = '存在绝对路径'
        abs_path_pattern = r'"\/(\/[^\/\n]*)+"'
        abs_info = list()
        abs_iter = re.finditer(abs_path_pattern, line[1])
        for match in abs_iter:
            path = match.group().strip('"')
            if path.startswith('//build') or path.startswith('//third_party'):
                break
            abs_info.append(path)
        if len(abs_info) > 0:
            pos = "line:{}  {}".format(line[0], line[1])
            self.err_info.append([key, pos, rules, issue])
            self.status = False
        return

    def check_pn_sn(self) -> None:
        rules = '规则3.2 部件编译目标必须指定部件和子系统名'
        target_pattern = r"^( *)("
        for target in self.TARGET_NAME:
            target_pattern += target
            if target != self.TARGET_NAME[-1]:
                target_pattern += r'|'
        target_pattern += r")[\s|\S]*?\n\1}$"
        check_list = ['subsystem_name', 'part_name']
        gn_data_merge = self.merge_line()
        for key, values in gn_data_merge.items():
            for white_repo in self.whitelist:
                if key.startswith(white_repo):
                    break
            else:
                for line in values:
                    targets = re.finditer(target_pattern, line[2], re.M)
                    for it_target in targets:
                        flag = {check_list[0]: False, check_list[1]: False}
                        target = it_target.group()
                        start_target = target.split('\n')[0]
                        target_pos = line[2].find(start_target)
                        line_offset = line[2].count('\n', 1, target_pos)

                        if target.find(check_list[0]) == -1:
                            flag[check_list[0]] = True
                        if target.find(check_list[1]) == -1:
                            flag[check_list[1]] = True
                        if any(flag.values()):
                            issue = 'target不存在'
                            issue += check_list[0] if flag[check_list[0]] else ''
                            issue += ',' if all(flag.values()) else ''
                            issue += check_list[1] if flag[check_list[1]] else ''
                            pos = "line:{}  {}".format(
                                line[0] + line_offset, start_target)
                            self.err_info.append([key, pos, rules, issue])
                            self.status = False

        return

    def check(self):
        if not self.gn_data:
            return
        for key, values in self.gn_data.items():
            for white_repo in self.whitelist:
                if key.startswith(white_repo):
                    break
            else:
                for line in values:
                    self.check_have_product_name(key, line)
                    self.check_abs_path(key, line)
        self.check_pn_sn()

    def output(self):
        self.check()
        
        return self.status, self.err_info


if __name__ == "__main__":
    data = {'a.gn': [[11, 'dsfsdf product_name'], [13, '("//build/dasd/")']],
            'b.gn': [[4, 'sdfd'],
                     [5, 'ohos_shared_library("librawfile") {'],
                     [14, 'sdfd'],
                     [15, 'ohos_shared_library("librawfile") {'],
                     [16, '  include_dirs = ['],
                     [17, '    "//base/global/resource_management/frameworks/resmgr/include",'],
                     [18, '  subsystem_name = "global"'], [19, '}'],
                     [25, '  subsystem_name = "global"'], [29, '}']]}

    a = CheckGnOnline(data)
    a.output()
    exit(0)
