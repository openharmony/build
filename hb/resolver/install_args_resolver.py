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
from modules.interface.install_module_interface import InstallModuleInterface
from util.component_util import ComponentUtil
from exceptions.ohos_exception import OHOSException
from services.hpm import CMDTYPE


class InstallArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    @staticmethod
    def resolve_part(target_arg: Arg, install_module: InstallModuleInterface):
        part_name = target_arg.arg_value
        if len(sys.argv) > 2 and not sys.argv[2].startswith("-"): # 第一个部件名参数
            part_name = sys.argv[2]
        if part_name:
            install_module.hpm.regist_flag('part_name', part_name)

    
    @staticmethod
    def resolve_global(target_arg: Arg, install_module: InstallModuleInterface):
        if target_arg.arg_value == True or target_arg.arg_value == '':
            install_module.hpm.regist_flag('global', '')

    @staticmethod
    def resolve_local(target_arg: Arg, install_module: InstallModuleInterface):
        if target_arg.arg_value:
            install_module.hpm.regist_flag('local', target_arg.arg_value)

    @staticmethod
    def resolve_variant(target_arg: Arg, install_module: InstallModuleInterface):
        if target_arg.arg_value:
            install_module.hpm.regist_flag('defaultDeps', ComponentUtil.get_default_deps(target_arg.arg_value))
        else:
            install_module.hpm.regist_flag('defaultDeps', ComponentUtil.get_default_deps("default"))