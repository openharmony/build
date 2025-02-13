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

from modules.interface.indep_build_module_interface import IndepBuildModuleInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from util.log_util import LogUtil
from containers.status import throw_exception
from resolver.indep_build_args_resolver import get_part_name
from containers.arg import BuildPhase


class OHOSIndepBuildModule(IndepBuildModuleInterface):
    _instance = None

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface, hpm: BuildFileGeneratorInterface,
                 indep_build: BuildFileGeneratorInterface):
        super().__init__(args_dict, args_resolver)
        self._hpm = hpm
        self._indep_build = indep_build
        OHOSIndepBuildModule._instance = self

    @property
    def hpm(self):
        return self._hpm

    @property
    def indep_build(self):
        return self._indep_build

    @staticmethod
    def get_instance():
        if OHOSIndepBuildModule._instance is not None:
            return OHOSIndepBuildModule._instance
        else:
            raise OHOSException(
                'OHOSIndepBuildModule has not been instantiated', '0000')

    @throw_exception
    def run(self):
        try:
            super().run()
        except OHOSException as exception:
            raise exception
        else:
            LogUtil.hb_info('{} build success'.format(','.join(get_part_name())))

    def _target_compilation(self):
        self._run_hpm()
        self._run_indep_build()

    def _run_hpm(self):
        self._run_phase(BuildPhase.HPM_DOWNLOAD)
        self.hpm.run()

    def _run_indep_build(self):
        self._run_phase(BuildPhase.INDEP_COMPILATION)
        self.indep_build.run()

    def _run_phase(self, phase: BuildPhase):
        '''Description: Traverse all registered parameters in build process and 
            execute the resolver function of the corresponding phase
        @parameter: [phase]:  Build phase corresponding to parameter
        @return :none
        '''
        for arg in self.args_dict.values():
            if isinstance(arg.arg_phase, list):
                if phase in arg.arg_phase:
                    self.args_resolver.resolve_arg(arg, self)
            else:
                if phase == arg.arg_phase:
                    self.args_resolver.resolve_arg(arg, self)
