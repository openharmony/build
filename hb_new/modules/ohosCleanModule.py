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

from containers.arg import CleanPhase
from modules.interface.cleanModuleInterface import CleanModuleInterface
from resolver.interface.argsResolver import ArgsResolver
from exceptions.ohosException import OHOSException


class OHOSCleanModule(CleanModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, argsResolver: ArgsResolver):
        super().__init__(args_dict, argsResolver)
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
        for phase_arg in [arg for arg in self.args_dict.values()if arg.argPhase == phase]:
            self.argsResolver.resolveArg(phase_arg, self)
