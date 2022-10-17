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

from abc import abstractmethod

from modules.interface.moduleInterface import ModuleInterface
from resolver.interface.argsResolver import ArgsResolver

class EnvModuleInterface(ModuleInterface):
    
    def __init__(self, args_dict: dict, argsResolver: ArgsResolver):
        super().__init__(args_dict, argsResolver)

    @abstractmethod
    def env_check(self):
        pass

    @abstractmethod
    def env_install(self):
        pass
    
    def run(self):
        self.env_check()
        self.env_install()
        