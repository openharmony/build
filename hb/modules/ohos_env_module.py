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

from modules.interface.env_module_interface import EnvModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from exceptions.ohos_exception import OHOSException


class OHOSEnvModule(EnvModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface):
        super().__init__(args_dict, args_resolver)
        OHOSEnvModule._instance = self

    @staticmethod
    def get_instance():
        if OHOSEnvModule._instance is not None:
            return OHOSEnvModule._instance
        else:
            raise OHOSException(
                'OHOSEnvModule has not been instantiated', '0000')

    def env_check(self):
        self.args_resolver.resolve_arg(self.args_dict['check'], self)

    def env_install(self):
        self.args_resolver.resolve_arg(self.args_dict['install'], self)
