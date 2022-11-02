#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
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
#

from containers.arg import Arg
from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from services.gn import CMDTYPE
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from modules.interface.tool_module_interface import ToolModuleInterface
from util.component_util import ComponentUtil


class ToolArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_list_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in target_arg.arg_value:
            if '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        tool_module.gn.execute_gn_cmd(
            cmd_type=CMDTYPE.LS, out_dir=out_dir, args_list=args_list)

    @staticmethod
    def resolve_desc_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in target_arg.arg_value:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(
                        out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException(
                        'Invalid desc args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        tool_module.gn.execute_gn_cmd(
            cmd_type=CMDTYPE.DESC, out_dir=out_dir, args_list=args_list)

    @staticmethod
    def resolve_path_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in target_arg.arg_value:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(
                        out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException(
                        'Invalid path args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        tool_module.gn.execute_gn_cmd(
            cmd_type=CMDTYPE.PATH, out_dir=out_dir, args_list=args_list)

    @staticmethod
    def resolve_refs_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in target_arg.arg_value:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(
                        out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException(
                        'Invalid refs args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        tool_module.gn.execute_gn_cmd(
            cmd_type=CMDTYPE.REFS, out_dir=out_dir, args_list=args_list)

    @staticmethod
    def resolve_format_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        tool_module.gn.execute_gn_cmd(
            cmd_type=CMDTYPE.FORMAT, args_list=target_arg.arg_value)

    @staticmethod
    def resolve_clean_targets(target_arg: Arg, tool_module: ToolModuleInterface):
        out_dir = ''
        out_dir = target_arg.arg_value[0]
        tool_module.gn.execute_gn_cmd(cmd_type=CMDTYPE.CLEAN, out_dir=out_dir)
