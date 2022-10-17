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


from modules.interface.buildModuleInterface import BuildModuleInterface
from resolver.interface.argsResolverInterface import ArgsResolverInterface
from services.interface.preloadInterface import PreloadInterface
from services.interface.loadInterface import LoadInterface
from services.interface.buildFileGeneratorInterface import BuildFileGeneratorInterface
from services.interface.buildExecutorInterface import BuildExecutorInterface
from containers.arg import BuildPhase
from exceptions.ohosException import OHOSException
from util.systemUtil import SystemUtil
from util.logUtil import LogUtil
from containers.status import throw_exception


class OHOSBuildModule(BuildModuleInterface):

    _instance = None

    def __init__(self, args_dict: dict, argsResolver: ArgsResolverInterface, preloader: PreloadInterface,
                 loader: LoadInterface, targetGenerator: BuildFileGeneratorInterface, targetCompiler: BuildExecutorInterface):
        super().__init__(args_dict, argsResolver, preloader,
                         loader, targetGenerator, targetCompiler)
        OHOSBuildModule._instance = self
        self._start_time = SystemUtil.get_current_time()

    @property
    def build_time(self):
        return SystemUtil.get_current_time() - self._start_time

    @staticmethod
    def get_instance():
        if OHOSBuildModule._instance is not None:
            return OHOSBuildModule._instance
        else:
            raise OHOSException(
                'OHOSBuildModule has not been instantiated', '0000')

    @throw_exception
    def run(self):
        try:
            super().run()
        except OHOSException as exception:
            raise exception
        else:
            LogUtil.hb_info('Cost time:  {}'.format(self.build_time))

    def _prebuild(self):
        self._run_phase(BuildPhase.PRE_BUILD)

    def _preload(self):
        self._run_phase(BuildPhase.PRE_LOAD)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').argValue:
            self.preloader.run()

    def _load(self):
        self._run_phase(BuildPhase.LOAD)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').argValue:
            self.loader.run()

    def _preTargetGenerate(self):
        self._run_phase(BuildPhase.PRE_TARGET_GENERATE)

    def _targetGenerate(self):
        self._run_phase(BuildPhase.TARGET_GENERATE)
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get("fast_rebuild").argValue:
            self.targetGenerator.run()

    def _postTargetGenerate(self):
        self._run_phase(BuildPhase.POST_TARGET_GENERATE)

    def _preTargetCompilation(self):
        self._run_phase(BuildPhase.PRE_TARGET_COMPILATION)

    def _targetCompilation(self):
        self._run_phase(BuildPhase.TARGET_COMPILATION)
        if self.args_dict.get('build_only_gn', None) and not self.args_dict.get("build_only_gn").argValue:
            self.targetCompiler.run()

    def _postTargetCompilation(self):
        self._run_phase(BuildPhase.POST_TARGET_COMPILATION)

    def _postBuild(self):
        self._run_phase(BuildPhase.POST_BUILD)

    def _run_phase(self, phase: BuildPhase):
        for phase_arg in [arg for arg in self.args_dict.values()if arg.argPhase == phase]:
            self.argsResolver.resolveArg(phase_arg, self)
