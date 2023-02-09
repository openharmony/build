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

from containers.arg import CleanPhase
from modules.interface.clean_module_interface import CleanModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from exceptions.ohos_exception import OHOSException


class OHOSCleanModule(CleanModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface):
        super().__init__(args_dict, args_resolver)
        OHOSCleanModule._instance = self

    @staticmethod
    def get_instance():
        if OHOSCleanModule._instance is not None:
            return OHOSCleanModule._instance
        else:
            raise OHOSException(
                'OHOSCleanModule has not been instantiated', '0000')

    def clean_regular(self):
        self._run_phase(CleanPhase.REGULAR)

    def clean_deep(self):
        self._run_phase(CleanPhase.DEEP)

    def _run_phase(self, phase: CleanPhase):
        '''Description: Traverse all registered parameters in clean process and 
            execute the resolver function of the corresponding phase
        @parameter: [phase]:  Clean phase corresponding to parameter
        @return :none
        '''
        for phase_arg in [arg for arg in self.args_dict.values()if arg.arg_phase == phase]:
            self.args_resolver.resolve_arg(phase_arg, self)
