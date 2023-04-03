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
import stat
import json
import argparse
import re
import pandas as pd
from bundle_check.bundle_check_common import BundleCheckTools
from bundle_check.warning_info import BCWarnInfo


class OhosInfo:
    g_root_path = BundleCheckTools.get_root_path()
    g_ohos_version = BundleCheckTools.get_ohos_version(g_root_path)


def check_all_bundle_json(path:str) -> list:
    '''
    @func: 检查指定目录下所有 bundle.json 的文件规范。
    '''

    if os.path.isabs(path):
        target_path = path
    else:
        target_path = os.path.join(OhosInfo.g_root_path, os.path.normpath(path))

    cur_path = os.getcwd()
    os.chdir(target_path)

    all_bundle = get_all_bundle_json()
    all_error = []

    for bundle_json_path in all_bundle:
        bundle_path = bundle_json_path.strip()
        bundle = BundleJson(bundle_path)
        bundle_error = bundle.check()

        subsystem_name = bundle.subsystem_name
        component_name = bundle.component_name
        if len(subsystem_name) == 0:
            subsystem_name = "Unknow"
        if len(component_name) == 0:
            component_name = "Unknow"

        if not bundle_error:
            continue
        for item in bundle_error:
            item['rule'] = BCWarnInfo.CHECK_RULE_2_1
            item['path'] = bundle_path
            item['component'] = component_name
            item['subsystem'] = subsystem_name
        all_error.extend(bundle_error)
    count = len(all_error)

    print('-------------------------------')
    print('Bundle.json check successfully!')
    print('There are {} issues in total'.format(count))
    print('-------------------------------')
    os.chdir(cur_path)
    return all_error


def get_all_bundle_json(path:str = '.') -> list:
    '''
    @func: 获取所有源码工程中所有 bundle.json 文件。
    '''
    exclude_list = [
        r'"./out/*"',
        r'"./.repo/*"'
    ]
    cmd = "find {} -name {}".format(path, "bundle.json")
    for i in exclude_list:
        cmd += " ! -path {}".format(i)
    bundle_josn_list = os.popen(cmd).readlines()
    return bundle_josn_list


class BundlesCheck:
    '''导出全量检查的结果。'''

    @staticmethod
    def to_json(all_errors:dict,
                output_path:str = '.',
                output_name:str = 'all_bundle_error.json'):
        '''@func: 导出所有错误到 json 格式文件中。'''
        all_errors = check_all_bundle_json(OhosInfo.g_root_path)
        all_error_json = json.dumps(all_errors,
                                    indent=4,
                                    ensure_ascii=False,
                                    separators=(', ', ': '))
        out_path = os.path.normpath(output_path) + '/' + output_name

        flags = os.O_WRONLY | os.O_CREAT
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(out_path, flags, modes), 'w') as file:
            file.write(all_error_json)
        print("Please check " + out_path)

    @staticmethod
    def to_df(path:str = None) -> pd.DataFrame:
        '''将所有错误的 dict 数据类型转为 pd.DataFrame 类型。'''
        if path is None:
            path = OhosInfo.g_root_path
        else:
            path = os.path.join(OhosInfo.g_root_path, path)
        all_errors = check_all_bundle_json(path)
        columns = ['子系统', '部件', '文件', '违反规则', '详细', '说明']
        errors_list = []
        for item in all_errors:
            error_temp = [
                item['subsystem'],
                item['component'],
                item['path'],
                item['rule'],
                "line" + str(item['line']) + ": " + item['contents'],
                item['description']
            ]
            errors_list.append(error_temp)
        ret = pd.DataFrame(errors_list, columns=columns)
        return ret

    @staticmethod
    def to_excel(output_path:str = '.',
                 output_name:str = 'all_bundle_error.xlsx'):
        '''
        @func: 导出所有错误到 excel 格式文件中。
        '''
        err_df = BundlesCheck.to_df()
        outpath = os.path.normpath(output_path) + '/' + output_name
        err_df.to_excel(outpath, index=None)
        print('Please check ' + outpath)  


class BundleJson(object):
    '''以 bundle.josn 路径来初始化的对象，包含关于该 bundle.josn 的一些属性和操作。 
    @var:  
      - ``__all_errors`` : 表示该文件的所有错误列表。
      - ``__json`` : 表示将该 josn 文件转为 dict 类型后的内容。
      - ``__lines`` : 表示将该 josn 文件转为 list 类型后的内容。  
 
    @method:  
      - ``component_name()`` : 返回该 bundle.json 所在部件名。
      - ``subsystem_name()`` : 返回该 bundle.json 所在子系统名。
      - ``readlines()`` : 返回该 bundle.json 以每一行内容为元素的 list。
      - ``get_line_number(s)`` : 返回 s 字符串在该 bundle.josn 中的行号，未知则返回 0。
      - ``check()`` : 静态检查该 bundle.json，返回错误告警 list。
    '''

    def __init__(self, path:str) -> None:
        self.__all_errors = [] # 该文件的所有错误列表
        self.__json  = {} # 将该 josn 文件转为字典类型内容
        self.__lines = [] # 将该 josn 文件转为列表类型内容
        with open(path, 'r') as file:
            try:
                self.__json = json.load(file)
            except json.decoder.JSONDecodeError as error:
                raise ValueError("'" + path + "'" + " is not a json file.")
        with open(path, 'r') as file:
            self.__lines = file.readlines()

    @property
    def component_name(self) -> str:
        return self.__json.get('component').get('name')

    @property
    def subsystem_name(self) -> str: # 目前存在为空的情况
        return self.__json.get('component').get('subsystem')
    
    def readlines(self) -> list:
        return self.__lines
    
    def get_line_number(self, string) -> int:
        '''
        @func: 获取指定字符串所在行号。
        '''
        line_num = 0
        for line in self.__lines:
            line_num += 1
            if string in line:
                return line_num
        return 0

    def check(self) -> list:
        '''
        @func: 检查该 bundle.json 规范。
        '''
        err_name = self.check_name()
        err_version = self.check_version()
        err_segment = self.check_segment()
        err_component = self.check_component()
        if err_name:
            self.__all_errors.append(err_name)
        if err_version:
            self.__all_errors.append(err_version)
        if err_segment:
            self.__all_errors.extend(err_segment)
        if err_component:
            self.__all_errors.extend(err_component)

        return self.__all_errors

    # name
    def check_name(self) -> dict:
        bundle_error = dict(line=0, contents='"name"')

        if 'name' not in self.__json:
            bundle_error["description"] = BCWarnInfo.NAME_NO_FIELD
            return bundle_error
        
        name = self.__json['name']
        bundle_error["line"] = self.get_line_number('"name"')
        if not name: # 为空
            bundle_error["description"] = BCWarnInfo.NAME_EMPTY
            return bundle_error

        bundle_error["description"] = BCWarnInfo.NAME_FORMAT_ERROR + \
                BCWarnInfo.COMPONENT_NAME_FROMAT + \
                BCWarnInfo.COMPONENT_NAME_FROMAT_LEN
        match = re.match(r'^@[a-z]+/([a-z_]{1,63})$', name)
        if not match:
            return bundle_error
        match = re.match(r'^([a-z]+_){1,31}[a-z]+$', name.split('/')[1])
        if not match:
            return bundle_error

        return dict()

    # version
    def check_version(self) -> dict:
        bundle_error = dict(line=0, contents='version')

        if 'version' not in self.__json:
            bundle_error["description"] = BCWarnInfo.VERSION_NO_FIELD
            return bundle_error

        bundle_error["line"] = self.get_line_number('"version": ')
        if len(self.__json['version']) < 3: # example 3.1
            bundle_error["description"] = BCWarnInfo.VERSION_ERROR
            return bundle_error

        if self.__json['version'] != OhosInfo.g_ohos_version:
            bundle_error['description'] = BCWarnInfo.VERSION_ERROR + \
                ' current ohos version is: ' + OhosInfo.g_ohos_version
            return bundle_error
        return dict()

    # segment
    def check_segment(self) -> list:
        bundle_error_segment = []
        bundle_error = dict(line=0, contents='"segment"')

        if 'segment' not in self.__json:
            bundle_error["description"] = BCWarnInfo.SEGMENT_NO_FIELD
            bundle_error_segment.append(bundle_error)
            return bundle_error_segment

        bundle_error["line"] = self.get_line_number('"segment":')
        if 'destPath' not in self.__json['segment']:
            bundle_error["description"] = BCWarnInfo.SEGMENT_DESTPATH_NO_FIELD
            bundle_error_segment.append(bundle_error)
            return bundle_error_segment

        path = self.__json['segment']['destPath']
        bundle_error["line"] = self.get_line_number('"destPath":')
        bundle_error["contents"] = '"segment:destPath"'
        if not path:
            bundle_error["description"] = BCWarnInfo.SEGMENT_DESTPATH_EMPTY
            bundle_error_segment.append(bundle_error)
            return bundle_error_segment

        if type(path) != str:
            bundle_error["description"] = BCWarnInfo.SEGMENT_DESTPATH_UNIQUE
            bundle_error_segment.append(bundle_error)
            return bundle_error_segment
        
        if os.path.isabs(path):
            bundle_error["description"] = BCWarnInfo.SEGMENT_DESTPATH_ABS
            bundle_error_segment.append(bundle_error)
            return bundle_error_segment
        
        return bundle_error_segment

    # component
    def check_component(self) -> list:
        bundle_error_component = []

        if 'component' not in self.__json:
            bundle_error = dict(line=0, contents='"component"',
                                description=BCWarnInfo.COMPONENT_NO_FIELD)
            bundle_error_component.append(bundle_error)
            return bundle_error_component
        
        component = self.__json.get('component')
        component_line = self.get_line_number('"component":')
        self._check_component_name(component, component_line, bundle_error_component)
        self._check_component_subsystem(component, component_line, bundle_error_component)
        self._check_component_syscap(component, bundle_error_component)
        self._check_component_feature(component, bundle_error_component)
        self._check_component_ast(component, component_line, bundle_error_component)
        self._check_component_rom(component, component_line, bundle_error_component)
        self._check_component_ram(component, component_line, bundle_error_component)
        self._check_component_deps(component, component_line, bundle_error_component)

        return bundle_error_component

        # component name
    def _check_component_name(self, component, component_line, bundle_error_component):
        if 'name' not in component:
            bundle_error = dict(line=component_line,
                                contents='"component"',
                                description=BCWarnInfo.COMPONENT_NAME_NO_FIELD)
            bundle_error_component.append(bundle_error)
        else:
            bundle_error = dict(line=component_line + 1,
                                contents='"component:name"')  # 同名 "name" 暂用 "component" 行号+1
            if not component['name']:
                bundle_error["description"] = BCWarnInfo.COMPONENT_NAME_EMPTY
                bundle_error_component.append(bundle_error)
            elif 'name' in self.__json and '/' in self.__json['name']:
                if component['name'] != self.__json['name'].split('/')[1]:
                    bundle_error["description"] = BCWarnInfo.COMPONENT_NAME_VERACITY
                    bundle_error_component.append(bundle_error)
        
        # component subsystem
    def _check_component_subsystem(self, component, component_line,
                                   bundle_error_component):
        if 'subsystem' not in component:
            bundle_error = dict(line=component_line,
                                contents="component",
                                description=BCWarnInfo.COMPONENT_SUBSYSTEM_NO_FIELD)
            bundle_error_component.append(bundle_error)
        else:
            bundle_error = dict(line=self.get_line_number('"subsystem":'),
                                contents='"component:subsystem"')
            if not component['subsystem']:
                bundle_error["description"] = BCWarnInfo.COMPONENT_SUBSYSTEM_EMPTY
                bundle_error_component.append(bundle_error)
            elif not BundleCheckTools.is_all_lower(component['subsystem']):
                bundle_error["description"] = BCWarnInfo.COMPONENT_SUBSYSTEM_LOWCASE
                bundle_error_component.append(bundle_error)

        # component syscap 可选且可以为空
    def _check_component_syscap(self, component, bundle_error_component):
        if 'syscap' not in component:
            pass
        elif component['syscap']:
            bundle_error = dict(line=self.get_line_number('"syscap":'),
                                contents='"component:syscap"')
            err = [] # 收集所有告警
            for i in component['syscap']:
                # syscap string empty
                if not i:
                    err.append(BCWarnInfo.COMPONENT_SYSCAP_STRING_EMPTY)
                    continue
                match = re.match(r'^SystemCapability(\.[A-Z][a-zA-Z]{1,63}){2,6}$', i)
                if not match:
                    err.append(BCWarnInfo.COMPONENT_SYSCAP_STRING_FORMAT_ERROR)
            errs = list(set(err)) # 去重告警
            if errs:
                bundle_error["description"] = str(errs)
                bundle_error_component.append(bundle_error)
        
        # component feature 可选且可以为空
    def _check_component_feature(self, component, bundle_error_component):
        if 'features' not in component:
            return

        bundle_error = dict(line=self.get_line_number('"features":'),
                            contents='"component:features"')
        err = []
        for feature in component["features"]:
            if not feature: # syscap string empty
                err.append(BCWarnInfo.COMPONENT_FEATURES_STRING_EMPTY)
                continue

            match = re.match(r'(\w+)_feature_(\w+).*', feature)
            if not match:
                err.append(BCWarnInfo.COMPONENT_FEATURES_FORMAT_ERROR)
                continue

            _component_name = match.group(1)
            # _feature = match.group(2) # 暂无格式规范
            if _component_name != component["name"]:
                err.append(BCWarnInfo.COMPONENT_FEATURES_FORMAT_ERROR)
        errs = list(set(err))
        if errs:
            bundle_error["description"] = str(errs)
            bundle_error_component.append(bundle_error)
        return
        
        # component adapted_system_type
    def _check_component_ast(self, component, component_line, bundle_error_component):
        if 'adapted_system_type' not in component:
            bundle_error = dict(line=component_line, contents='"component"',
                                description=BCWarnInfo.COMPONENT_AST_NO_FIELD)
            bundle_error_component.append(bundle_error)
            return
        
        bundle_error = dict(line=self.get_line_number('"adapted_system_type":'),
                            contents='"component:adapted_system_type"')
        ast = component["adapted_system_type"]
        if not ast:
            bundle_error["description"] = BCWarnInfo.COMPONENT_AST_EMPTY
            bundle_error_component.append(bundle_error)
            return

        type_set = tuple(set(ast))
        if len(ast) > 3 or len(type_set) != len(ast):
            bundle_error["description"] = BCWarnInfo.COMPONENT_AST_NO_REP
            bundle_error_component.append(bundle_error)
            return

        all_type_list = ["mini", "small", "standard"]
        # 不符合要求的 type
        error_type = [i for i in ast if i not in all_type_list]
        if error_type:
            bundle_error["description"] = BCWarnInfo.COMPONENT_AST_NO_REP
            bundle_error_component.append(bundle_error)
        return

        # component rom
    def _check_component_rom(self, component, component_line, bundle_error_component):
        if 'rom' not in component:
            bundle_error = dict(line=component_line, contents='"component:rom"',
                                description=BCWarnInfo.COMPONENT_ROM_NO_FIELD)
            bundle_error_component.append(bundle_error)
        elif not component["rom"]:
            bundle_error = dict(line=self.get_line_number('"rom":'),
                                contents='"component:rom"',
                                description=BCWarnInfo.COMPONENT_ROM_EMPTY)
            bundle_error_component.append(bundle_error)
        else:
            bundle_error = dict(line=self.get_line_number('"rom":'),
                                contents='"component:rom"')
            num, unit = BundleCheckTools.split_by_unit(component["rom"])
            if num <= 0:
                bundle_error["description"] = BCWarnInfo.COMPONENT_ROM_SIZE_ERROR # 非数值或小于0
                bundle_error_component.append(bundle_error)
            elif unit:
                unit_list = ["KB", "KByte", "MByte", "MB"]
                if unit not in unit_list:
                    bundle_error["description"] = BCWarnInfo.COMPONENT_ROM_UNIT_ERROR # 单位有误
                    bundle_error_component.append(bundle_error)
            
        # component ram
    def _check_component_ram(self, component, component_line, bundle_error_component):
        if 'ram' not in component:
            bundle_error = dict(line=component_line, contents='"component:ram"',
                                description=BCWarnInfo.COMPONENT_RAM_NO_FIELD)
            bundle_error_component.append(bundle_error)
        elif not component["ram"]:
            bundle_error = dict(line=self.get_line_number('"ram":'),
                                contents='"component:ram"',
                                description=BCWarnInfo.COMPONENT_RAM_EMPTY)
            bundle_error_component.append(bundle_error)
        else:
            bundle_error = dict(line=self.get_line_number('"ram":'),
                                contents='"component:ram"')
            num, unit = BundleCheckTools.split_by_unit(component["ram"])
            if num <= 0:
                bundle_error["description"] = BCWarnInfo.COMPONENT_RAM_SIZE_ERROR # 非数值或小于0
                bundle_error_component.append(bundle_error)
            elif unit:
                unit_list = ["KB", "KByte", "MByte", "MB"]
                if unit not in unit_list:
                    bundle_error["description"] = BCWarnInfo.COMPONENT_RAM_UNIT_ERROR # 单位有误
                    bundle_error_component.append(bundle_error)

        # component deps
    def _check_component_deps(self, component, component_line, bundle_error_component):
        if 'deps' not in component:
            bundle_error = dict(line=component_line, contents='"component:deps"',
                                description=BCWarnInfo.COMPONENT_DEPS_NO_FIELD)
            bundle_error_component.append(bundle_error)
        else:
            pass


def parse_args():
    parser = argparse.ArgumentParser()
    # exclusive output format
    ex_format = parser.add_mutually_exclusive_group()
    ex_format.add_argument("--xlsx", help="output format: xls(default).",
                           action="store_true")
    ex_format.add_argument("--json", help="output format: json.",
                           action="store_true")
    # exclusive input
    ex_input = parser.add_mutually_exclusive_group()
    ex_input.add_argument("-P", "--project", help="project root path.", type=str)
    ex_input.add_argument("-p", "--path", help="bundle.json path list.", nargs='+')
    # output path
    parser.add_argument("-o", "--output", help="ouput path.")
    args = parser.parse_args()

    export_path = '.'
    if args.output:
        export_path = args.output

    if args.project:
        if not BundleCheckTools.is_project(args.project):
            print("'" + args.project + "' is not a oopeharmony project.")
            exit(1)
        
        if args.json:
            BundlesCheck.to_json(export_path)
        else:
            BundlesCheck.to_excel(export_path)
    elif args.path:
        bundle_list_error = {}
        for bundle_json_path in args.path:
            bundle = BundleJson(bundle_json_path)
            error_field = bundle.check()
            if error_field:
                bundle_list_error[bundle_json_path] = \
                    dict([(BCWarnInfo.CHECK_RULE_2_1, error_field)])
        # temp
        test_json = json.dumps(bundle_list_error,
                               indent=4, separators=(', ', ': '), 
                               ensure_ascii=False)
        print(test_json)
    else:
        print("use '-h' get help.")


if __name__ == '__main__':
    parse_args()
