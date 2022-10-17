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

from containers.arg import Arg
from modules.interface.moduleInterface import ModuleInterface
from resolver.interface.argsResolver import ArgsResolver

class CleanModuleInterface(ModuleInterface):
    
    def __init__(self, args_dict: dict, argsResolver: ArgsResolver):
        super().__init__(args_dict, argsResolver)
    
    @abstractmethod
    def clean_regular(self):
        pass
    
    @abstractmethod
    def clean_deep(self):
        pass
    
    def _get_all_abstract_method(self):
        return list(filter(lambda m: not m.startswith('_') 
                           and callable(getattr(self, m))
                           and m.startswith('clean')
                           and hasattr(m, __isabstractmethod__)
                           , dir(self)))
    
    def run(self):
        if self.args_dict['clean_all'].argValue:
            for arg in self.args_dict.values():
                if isinstance(arg, Arg):
                    arg.argValue = True
                    
        self.clean_regular()
        self.clean_deep()
        