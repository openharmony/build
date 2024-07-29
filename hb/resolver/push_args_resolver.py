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
from modules.interface.push_module_interface import PushModuleInterface
from util.component_util import ComponentUtil
from exceptions.ohos_exception import OHOSException
from services.hdc import CMDTYPE


class PushArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_part(target_arg: Arg, push_module: PushModuleInterface):
        part_name = target_arg.arg_value
        if len(sys.argv) > 2 and not sys.argv[2].startswith("-"): # 第一个部件名参数 
            part_name = sys.argv[2]
        if part_name:
            push_module.hdc.regist_flag('part_name', part_name)

    @staticmethod
    def resolve_target(target_arg: Arg, push_module: PushModuleInterface):
        if target_arg.arg_value:
            push_module.hdc.regist_flag('target', target_arg.arg_value)
        else:
            raise OHOSException('ERROR argument "hb push no target set". ')
    
    @staticmethod
    def resolve_list_targets(target_arg: Arg, push_module: PushModuleInterface):
        if target_arg.arg_value:
            push_module.hdc.execute_hdc_cmd(CMDTYPE.LIST_TARGETS)
            Arg.write_args_file("list_targets", False, ModuleType.PUSH)

    @staticmethod
    def resolve_reboot(target_arg: Arg, push_module: PushModuleInterface):
        if target_arg.arg_value:
            push_module.hdc.regist_flag('reboot', True)
    
    @staticmethod
    def resolve_src(target_arg: Arg, push_module: PushModuleInterface):
        if target_arg.arg_value:
            push_module.hdc.regist_flag('src', target_arg.arg_value)
            Arg.write_args_file("src", "", ModuleType.PUSH)