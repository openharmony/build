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
from services.interface.preload import Preload
from services.interface.load import Load
from services.interface.buildExecutor import BuildExecutor
from services.interface.buildFileGenerator import BuildFileGenerator
from resolver.interface.argsResolver import ArgsResolver
from containers.statusCode import StatusCode


class BuildModuleInterface(ModuleInterface):

    def __init__(self, args_dict: dict, argsResolver: ArgsResolver, preloader: Preload, loader: Load,
                 targetGenerator: BuildFileGenerator, targetCompiler: BuildExecutor):
        super().__init__(args_dict, argsResolver)
        self._loader = loader
        self._preloader = preloader
        self._targetGenerator = targetGenerator
        self._targetCompiler = targetCompiler

    @property
    def preloader(self):
        return self._preloader

    @property
    def loader(self):
        return self._loader

    @property
    def targetGenerator(self):
        return self._targetGenerator

    @property
    def targetCompiler(self):
        return self._targetCompiler

    def run(self) -> StatusCode:
        try:
            self._prebuild()
            self._preload()
            self._load()
            self._preTargetGenerate()
            self._targetGenerate()
            self._postTargetGenerate()
            self._preTargetCompilation()
            self._targetCompilation()
            self._postTargetCompilation()
        except Exception:
            raise
        finally:
            self._postBuild()

    @abstractmethod
    def _prebuild(self):
        pass

    @abstractmethod
    def _preload(self):
        pass

    @abstractmethod
    def _load(self):
        pass

    @abstractmethod
    def _preTargetGenerate(self):
        pass

    @abstractmethod
    def _targetGenerate(self):
        pass

    @abstractmethod
    def _postTargetGenerate(self):
        pass

    @abstractmethod
    def _preTargetCompilation(self):
        pass

    @abstractmethod
    def _targetCompilation(self):
        pass

    @abstractmethod
    def _postTargetCompilation(self):
        pass

    @abstractmethod
    def _postBuild(self):
        pass
