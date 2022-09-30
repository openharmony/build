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

from resources.config import Config
from modules.interface.buildModuleInterface import BuildModuleInterface
from resolver.interface.argsResolver import ArgsResolver
from services.interface.preload import Preload
from services.interface.load import Load
from services.interface.buildFileGenerator import BuildFileGenerator
from services.interface.buildExecutor import BuildExecutor
from containers.statusCode import StatusCode
from containers.arg import BuildPhase


class OHOSBuildModule(BuildModuleInterface):

    def __init__(self, args_dict: dict, argsResolver: ArgsResolver, preloader: Preload,
                 loader: Load, targetGenerator: BuildFileGenerator, targetCompiler: BuildExecutor):
        super().__init__(args_dict, argsResolver, preloader,
                         loader, targetGenerator, targetCompiler)
        self._config = Config()

    @property
    def config(self):
        return self._config

    def _prebuild(self) -> StatusCode:
        return self._run_phase(BuildPhase.PRE_BUILD)

    def _preload(self) -> StatusCode:
        status_code = self._run_phase(BuildPhase.PRE_LOAD)
        if not status_code.status:
            return status_code
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').argValue:
            return self.preloader.run()

    def _load(self) -> StatusCode:
        status_code = self._run_phase(BuildPhase.LOAD)
        if not status_code.status:
            return status_code
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get('fast_rebuild').argValue:
            return self.loader.run()

    def _preTargetGenerate(self) -> StatusCode:
        return self._run_phase(BuildPhase.PRE_TARGET_GENERATE)

    def _targetGenerate(self) -> StatusCode:
        status_code = self._run_phase(BuildPhase.TARGET_GENERATE)
        if not status_code.status:
            return status_code
        if self.args_dict.get('fast_rebuild', None) and not self.args_dict.get("fast_rebuild").argValue:
            return self.targetGenerator.run()

    def _postTargetGenerate(self) -> StatusCode:
        return self._run_phase(BuildPhase.POST_TARGET_GENERATE)

    def _preTargetCompilation(self) -> StatusCode:
        return self._run_phase(BuildPhase.PRE_TARGET_COMPILATION)

    def _targetCompilation(self) -> StatusCode:
        status_code = self._run_phase(BuildPhase.TARGET_COMPILATION)
        if not status_code.status:
            return status_code
        if self.args_dict.get('build_only_gn', None) and not self.args_dict.get("build_only_gn").argValue:
            return self.targetCompiler.run()

    def _postTargetCompilation(self) -> StatusCode:
        return self._run_phase(BuildPhase.POST_TARGET_COMPILATION)

    def _postBuild(self) -> StatusCode:
        return self._run_phase(BuildPhase.POST_BUILD)

    def _run_phase(self, phase: BuildPhase) -> StatusCode:
        for phase_arg in [arg for arg in self.args_dict.values()if arg.argPhase == phase]:
            status_code = self.argsResolver.resolveArg(
                phase_arg, self, config=self.config)
            if not status_code.status:
                return status_code
        return StatusCode()
