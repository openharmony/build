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
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from containers.arg import ModuleType
from containers.arg import Arg


class ToolModuleInterface(ModuleInterface):

    def __init__(self, args_dict: dict, argsResolver: ArgsResolverInterface):
        super().__init__(args_dict, argsResolver)

    @abstractmethod
    def list_targets(self):
        pass
    
    @abstractmethod
    def desc_targets(self):
        pass
    
    @abstractmethod
    def path_targets(self):
        pass
    
    @abstractmethod
    def refs_targets(self):
        pass
    
    @abstractmethod
    def format_targets(self):
        pass
    
    @abstractmethod
    def clean_targets(self):
        pass

    def run(self):
        if self.args_dict['ls'].argValue:
            self.list_targets()
        elif self.args_dict['desc'].argValue:
            self.desc_targets()
        elif self.args_dict['path'].argValue:
            self.path_targets()
        elif self.args_dict['refs'].argValue:
            self.refs_targets()
        elif self.args_dict['format'].argValue:
            self.format_targets()
        elif self.args_dict['clean'].argValue:
            self.clean_targets()
        else:
            Arg.get_help(ModuleType.TOOL)
