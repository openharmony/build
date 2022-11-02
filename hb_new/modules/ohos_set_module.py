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

from modules.interface.set_module_interface import SetModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from services.interface.menu_interface import MenuInterface
from exceptions.ohos_exception import OHOSException


class OHOSSetModule(SetModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface, menu: MenuInterface):
        super().__init__(args_dict, args_resolver)
        self._menu = menu
        OHOSSetModule._instance = self

    @staticmethod
    def get_instance():
        if OHOSSetModule._instance is not None:
            return OHOSSetModule._instance
        else:
            raise OHOSException(
                'OHOSSetModule has not been instantiated', '0000')

    @property
    def menu(self):
        return self._menu

    def set_product(self):
        self.args_resolver.resolve_arg(self.args_dict['product_name'], self)

    def set_parameter(self):
        self.args_resolver.resolve_arg(self.args_dict['all'], self)
