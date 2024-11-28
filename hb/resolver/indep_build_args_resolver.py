#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2023 Huawei Device Co., Ltd.
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
#

import os
import sys

from containers.arg import Arg
from containers.arg import ModuleType
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from modules.interface.indep_build_module_interface import IndepBuildModuleInterface
from util.component_util import ComponentUtil
from exceptions.ohos_exception import OHOSException


def get_part_name():
    part_name_list = []
    if len(sys.argv) > 2 and not sys.argv[2].startswith("-"):           
        for name in sys.argv[2:]:
            if not name.startswith('-'):
                part_name_list.append(name)
            else:
                break
    return part_name_list


class IndepBuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_target_cpu(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        if target_arg.arg_value:
            build_executor.regist_flag('cpu', target_arg.arg_value)
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("target_cpu")
            build_executor.regist_flag('cpu', arg.get("argDefault"))

    @staticmethod
    def resolve_target_os(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        if target_arg.arg_value:
            build_executor.regist_flag('os', target_arg.arg_value)
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("target_os")
            build_executor.regist_flag('os', arg.get("argDefault"))

    @staticmethod
    def resolve_part(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        '''
        编译部件名获取优先级： hb build 指定的部件名参数  > hb build 在部件源码仓运行时通过找到bundle.json获取到的部件名 > hb env 设置的部件名参数
        '''
        build_executor = indep_build_module.hpm
        target_arg.arg_value_list = get_part_name()

        if target_arg.arg_value_list:
            bundle_path_list = []
            for path in target_arg.arg_value_list:
                try:
                    print("collecting bundle.json, please wait")
                    bundle_path = ComponentUtil.search_bundle_file(path)
                    print("collect done")
                    bundle_path_list.append(bundle_path)
                except Exception as e:
                    raise OHOSException('Please check the bundle.json file of {} : {}'.format(path, e))
                if not bundle_path:
                    print('ERROR argument "hb build <part_name>": Invalid part_name "{}". '.format(path))
                    sys.exit(1)
            build_executor.regist_flag('path', ','.join(bundle_path_list))
        elif ComponentUtil.is_in_component_dir(os.getcwd()):
            part_name, bundle_path = ComponentUtil.get_component(os.getcwd())
            if part_name:
                target_arg.arg_value_list = part_name
                build_executor.regist_flag('path', bundle_path)
            else:
                raise OHOSException('ERROR argument "no bundle.json": Invalid directory "{}". '.format(os.getcwd()))
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("part")
            if arg.get("argDefault"):
                bundle_path = ComponentUtil.search_bundle_file(arg.get("argDefault"))
                if not bundle_path:
                    raise OHOSException('ERROR argument "hb env --part <part_name>": Invalid part_name "{}". '.format(
                        target_arg.arg_value_list))
                build_executor.regist_flag('path', bundle_path)
            else:
                raise OHOSException('ERROR argument "hb build <part_name>": no part_name . ')

    @staticmethod
    def resolve_variant(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        if target_arg.arg_value:
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps(target_arg.arg_value, True if '-t' in sys.argv else False))
            build_executor.regist_flag('variant', target_arg.arg_value)
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("variant")
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps("argDefault"))
            build_executor.regist_flag('variant', arg.get("argDefault"))
    
    @staticmethod
    def resolve_branch(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        if target_arg.arg_value:
            build_executor.regist_flag('branch', target_arg.arg_value)
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg = args_dict.get("branch")
            build_executor.regist_flag('branch', "argDefault")
