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
import os

from resources.config import Config
from modules.interface.buildModuleInterface import BuildModuleInterface
from resolver.interface.argsResolver import ArgsResolver
from services.interface.preload import Preload
from services.interface.load import Load
from services.interface.buildFileGenerator import BuildFileGenerator
from services.interface.buildExecutor import BuildExecutor
from containers.statusCode import StatusCode


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
        for prebuildArg in [arg for arg in self.args_dict.values() if arg.argPhase == 'prebuild']:
            status_code = self.argsResolver.resolveArg(prebuildArg, self, self.config)
            if not status_code.status:
                return status_code
        return StatusCode()

    def _preload(self) -> StatusCode:
        for preloadArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'preload']:
            status_code = self.argsResolver.resolveArg(
                preloadArg, self, self.config)
            if not status_code.status:
                return status_code

        return self.preloader.run()

    def _load(self) -> StatusCode:
        for preloadArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'loader']:
            status_code = self.argsResolver.resolveArg(
                preloadArg, self, config=self.config)
            if not status_code.status:
                return status_code
        return self.loader.run()

    def _preTargetGenerate(self) -> StatusCode:
        for preTargetGenerateArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'preTargetGenerate']:
            status_code = self.argsResolver.resolveArg(
                preTargetGenerateArg, self, config=self.config)
            if not status_code.status:
                return status_code 
        return StatusCode()

    def _targetGenerate(self) -> StatusCode:
        for targetGenerateArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'targetGenerate']:
            status_code = self.argsResolver.resolveArg(
                targetGenerateArg, self, config=self.config)
            if not status_code.status:
                return status_code

        return self.targetGenerator.run()

    def _postTargetGenerate(self) -> StatusCode:
        for postTargetGenerateArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'postTargetGenerate']:
            status_code = self.argsResolver.resolveArg(
                postTargetGenerateArg, self, config=self.config)
            if not status_code.status:
                return status_code

    def _preTargetCompilation(self) -> StatusCode:
        for preTargetCompilationArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'preTargetCompilation']:
            status_code = self.argsResolver.resolveArg(
                preTargetCompilationArg, self, config=self.config)
            if status_code == 0:
                return status_code

    def _targetCompilation(self) -> StatusCode:
        for targetCompilationArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'targetCompilation']:
            status_code = self.argsResolver.resolveArg(
                targetCompilationArg, self, config=self.config)
            if status_code == 0:
                return status_code

        return self.targetCompiler.run()

    def _postTargetCompilation(self) -> StatusCode:
        for postTargetCompilationArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'postTargetCompilation']:
            status_code = self.argsResolver.resolveArg(
                postTargetCompilationArg, self, config=self.config)
            if status_code == 0:
                return status_code

    def _postBuild(self) -> StatusCode:
        for postBuildArg in [arg for arg in self.args_dict.values()if arg.argPhase == 'postbuild']:
            status_code = self.argsResolver.resolveArg(
                postBuildArg, self, config=self.config)
            if status_code == 0:
                return status_code
