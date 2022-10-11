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

import os

from containers.arg import Arg
from containers.arg import ModuleType
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from modules.interface.setModuleInterface import SetModuleInterface
from exceptions.ohosException import OHOSException
from resources.config import Config
from util.productUtil import ProductUtil
from util.deviceUtil import DeviceUtil
from containers.status import throw_exception


class SetArgsResolver(ArgsResolverInterface):

    def __init__(self, args_dict: dict):
        super().__init__(args_dict)

    def resolveProductName(self, targetArg: Arg, setModule: SetModuleInterface):
        config = Config()
        product_info = dict()
        device_info = dict()
        if targetArg.argValue == '':
            product_info = setModule._menu.select_product()
        elif targetArg.argValue.__contains__('@'):
            product_name, company_name = targetArg.argValue.split('@', 2)
            product_info = ProductUtil.get_product_info(
                product_name, company_name)
        else:
            product_info = ProductUtil.get_product_info(targetArg.argValue)

        config.product = product_info.get('name')
        config.product_path = product_info.get('product_path')
        config.version = product_info.get('version')
        config.os_level = product_info.get('os_level')
        config.product_json = product_info.get('config')
        config.component_type = product_info.get('component_type')
        if product_info.get('product_config_path'):
            config.product_config_path = product_info.get(
                'product_config_path')
        else:
            config.product_config_path = product_info.get('path')

        device_info = ProductUtil.get_device_info(config.product_json)
        config.board = device_info.get('board')
        config.kernel = device_info.get('kernel')
        config.target_cpu = device_info.get('target_cpu')
        config.target_os = device_info.get('target_os')
        config.support_cpu = device_info.get("support_cpu")
        kernel_version = device_info.get('kernel_version')
        config.device_company = device_info.get('company')
        board_path = device_info.get('board_path')

        if product_info.get('build_out_path'):
            config.out_path = os.path.join(config.root_path,
                                           product_info.get('build_out_path'))
        else:
            if config.os_level == 'standard':
                config.out_path = os.path.join(config.root_path, 'out',
                                               config.board)
            else:
                config.out_path = os.path.join(config.root_path, 'out',
                                               config.board, config.product)

        if product_info.get('subsystem_config_json'):
            config.subsystem_config_json = product_info.get(
                'subsystem_config_json')
        else:
            config.subsystem_config_json = 'build/subsystem_config.json'

        if config.version == '2.0':
            config.device_path = board_path
        else:
            if config.os_level == "standard":
                config.device_path = board_path
            else:
                config.device_path = DeviceUtil.get_device_path(
                    board_path, config.kernel, kernel_version)

        if device_info.get('board_config_path'):
            config.device_config_path = device_info.get('board_config_path')
        else:
            config.device_config_path = config.device_path

        Arg.write_args_file(targetArg.argName,
                            product_info.get('name'), ModuleType.BUILD)
        Arg.write_args_file(targetArg.argName,
                            product_info.get('name'), ModuleType.SET)

    def resolveSetParameter(self, targetArg: Arg, setModule: SetModuleInterface):
        if targetArg.argValue:
            self.resolveProductName(
                setModule.args_dict['product_name'], setModule)
            options = setModule.menu.select_compile_option()
            for argName, argVaule in options.items():
                Arg.write_args_file(argName, argVaule, ModuleType.BUILD)
    
    @throw_exception
    def _mapArgsToFunction(self, args_dict: dict):
        for entity in args_dict.values():
            if isinstance(entity, Arg):
                argsName = entity.argName
                functionName = entity.resolveFuntion
                if not hasattr(self, functionName) or \
                        not hasattr(self.__getattribute__(functionName), '__call__'):
                    raise OHOSException(
                        f'There is no resolution for arg: ' + argsName, '0000')
                entity.resolveFuntion = self.__getattribute__(functionName)
                self._argsToFunction[argsName] = self.__getattribute__(
                    functionName)
