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

from abc import abstractmethod
from modules.interface.module_interface import ModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface


class CleanModuleInterface(ModuleInterface):

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface):
        super().__init__(args_dict, args_resolver)

    @abstractmethod
    def clean_regular(self):
        pass

    @abstractmethod
    def clean_deep(self):
        pass

    def run(self):
        self.clean_regular()
        self.clean_deep()
