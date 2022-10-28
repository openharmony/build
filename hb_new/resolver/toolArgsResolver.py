#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2020 Huawei Device Co., Ltd.
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
from exceptions.ohosException import OHOSException
from services.gn import CMDTYPE
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from modules.interface.toolModuleInterface import ToolModuleInterface
from util.componentUtil import ComponentUtil


class ToolArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)
        
    @staticmethod
    def resolveListTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in targetArg.argValue:
            if '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.LS, out_dir=out_dir, args_list=args_list)
            
    @staticmethod
    def resolveDescTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in targetArg.argValue:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException('Invalid desc args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.DESC, out_dir=out_dir, args_list=args_list)
        
    @staticmethod
    def resolvePathTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in targetArg.argValue:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException('Invalid path args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.PATH, out_dir=out_dir, args_list=args_list)
        
    @staticmethod
    def resolveRefsTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        out_dir = ''
        args_list = []
        for arg in targetArg.argValue:
            if ':' in arg:
                try:
                    component_name, module_name = arg.split(':')
                    args_list.append(ComponentUtil.get_component_module_full_name(out_dir, component_name, module_name))
                except Exception:
                    raise OHOSException('Invalid refs args: {} ,need <component:module>'.format(arg))
            elif '-' not in arg and len(out_dir) == 0:
                out_dir = arg
            else:
                args_list.append(arg)
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.REFS, out_dir=out_dir, args_list=args_list)
        
    @staticmethod
    def resolveFormatTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.FORMAT, args_list=targetArg.argValue)
        
    @staticmethod
    def resolveCleanTargets(targetArg: Arg, toolModule: ToolModuleInterface):
        out_dir = ''
        out_dir = targetArg.argValue[0]
        toolModule.gn.execute_gn_cmd(cmd_type=CMDTYPE.CLEAN, out_dir=out_dir)
