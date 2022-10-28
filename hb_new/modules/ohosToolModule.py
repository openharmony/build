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

from modules.interface.toolModuleInterface import ToolModuleInterface
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from services.interface.buildFileGeneratorInterface import BuildFileGeneratorInterface
from exceptions.ohosException import OHOSException


class OHOSToolModule(ToolModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, argsResolver: ArgsResolverInterface, gn: BuildFileGeneratorInterface):
        super().__init__(args_dict, argsResolver)
        self._gn = gn
        OHOSToolModule._instance = self

    @staticmethod
    def get_instance():
        if OHOSToolModule._instance is not None:
            return OHOSToolModule._instance
        else:
            raise OHOSException(
                'OHOSToolModule has not been instantiated', '0000')
    @property
    def gn(self):
        return self._gn

    def list_targets(self):
        self.argsResolver.resolveArg(self.args_dict['ls'], self)
        
    def desc_targets(self):
        self.argsResolver.resolveArg(self.args_dict['desc'], self)
        
    def path_targets(self):
        self.argsResolver.resolveArg(self.args_dict['path'], self)
        
    def refs_targets(self):
        self.argsResolver.resolveArg(self.args_dict['refs'], self)
        
    def format_targets(self):
        self.argsResolver.resolveArg(self.args_dict['format'], self)
        
    def clean_targets(self):
        self.argsResolver.resolveArg(self.args_dict['clean'], self)
