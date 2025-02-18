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


def _search_bundle_path(part_name: str) -> str:
    bundle_path = None
    try:
        bundle_path = ComponentUtil.search_bundle_file(part_name)
    except Exception as e:
        raise OHOSException('Please check the bundle.json file of {} : {}'.format(part_name, e))
    if not bundle_path:
        print('ERROR argument "hb build <part_name>": Invalid part_name "{}". '.format(part_name))
        sys.exit(1)
    return bundle_path


class IndepBuildArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_target_cpu(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("target_cpu").get("argDefault")
        build_executor.regist_flag('cpu', arg_value)
        Arg.write_args_file("target_cpu", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_target_os(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("target_os").get("argDefault")
        build_executor.regist_flag('os', arg_value)
        Arg.write_args_file("target_os", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_part(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        '''
        编译部件名获取优先级： hb build 指定的部件名参数  > hb build 在部件源码仓运行时通过找到bundle.json获取到的部件名 > hb env 设置的部件名参数
        '''
        hpm_executor = indep_build_module.hpm
        indep_build_executor = indep_build_module.indep_build
        target_arg.arg_value_list = get_part_name()
        arg_value = ""

        if target_arg.arg_value_list:
            if hasattr(IndepBuildArgsResolver, "bundle_path_ccache"):
                arg_value = IndepBuildArgsResolver.bundle_path_ccache
            else:
                bundle_path_list = []
                print("collecting bundle.json, please wait")
                for part_name in target_arg.arg_value_list:
                    bundle_path = _search_bundle_path(part_name)
                    bundle_path_list.append(bundle_path)
                print("collect done")
                arg_value = ','.join(bundle_path_list)
                IndepBuildArgsResolver.bundle_path_ccache = arg_value
        elif ComponentUtil.is_in_component_dir(os.getcwd()):
            part_name, bundle_path = ComponentUtil.get_component(os.getcwd())
            if part_name:
                target_arg.arg_value_list = part_name
                arg_value = bundle_path
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
                arg_value = bundle_path
            else:
                raise OHOSException('ERROR argument "hb build <part_name>": no part_name . ')
        hpm_executor.regist_flag('path', arg_value)
        indep_build_executor.regist_flag('path', arg_value)
        Arg.write_args_file("part", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_variant(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps(target_arg.arg_value,
                                                                                     True if '-t' in sys.argv else False))
            arg_value = target_arg.arg_value
        else:
            build_executor.regist_flag('defaultDeps', ComponentUtil.get_default_deps("argDefault"))
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("variant").get("argDefault")

        build_executor.regist_flag('variant', arg_value)
        indep_build_module.indep_build.regist_flag('variant', arg_value)
        Arg.write_args_file("variant", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_branch(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        build_executor = indep_build_module.hpm
        arg_value = ""
        if target_arg.arg_value:
            arg_value = target_arg.arg_value
        else:
            args_dict = Arg.read_args_file(ModuleType.ENV)
            arg_value = args_dict.get("branch").get("argDefault")
        build_executor.regist_flag('branch', arg_value)
        Arg.write_args_file("branch", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_build_type(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        arg_value = ""
        if (sys.argv[1] == 'build' and
                '-i' in sys.argv[3:] and
                {'-t', '-test'} & set(sys.argv[3:])):
            arg_value = "both"
        elif (sys.argv[1] == 'build' and
              '-i' not in sys.argv[3:] and
              (sys.argv[-1] == "-t" or ("-t" in sys.argv and sys.argv[sys.argv.index("-t") + 1][0] == '-'))):
            arg_value = "onlytest"
        else:
            arg_value = "onlysrc"
            indep_build_module.indep_build.regist_flag("buildType", "onlysrc")
        if arg_value != "onlysrc":
            indep_build_module.hpm.regist_flag("buildType", arg_value)
        indep_build_module.indep_build.regist_flag("buildType", arg_value)
        Arg.write_args_file("build_type", arg_value, ModuleType.INDEP_BUILD)

    @staticmethod
    def resolve_keep_ninja_going(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('keep-ninja-going', target_arg.arg_value)

    @staticmethod
    def resolve_gn_args(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('gn-args', target_arg.arg_value)

    @staticmethod
    def resolve_skip_download(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.hpm.regist_flag('skip-download', target_arg.arg_value)

    @staticmethod
    def resolve_build_target(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('build-target', target_arg.arg_value)

    @staticmethod
    def resolve_fast_rebuild(target_arg: Arg, indep_build_module: IndepBuildModuleInterface):
        indep_build_module.indep_build.regist_flag('fast-rebuild', target_arg.arg_value)
