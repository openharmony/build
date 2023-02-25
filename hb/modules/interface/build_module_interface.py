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

from abc import abstractmethod
from exceptions.ohos_exception import OHOSException
from modules.interface.module_interface import ModuleInterface
from services.interface.preload_interface import PreloadInterface
from services.interface.load_interface import LoadInterface
from services.interface.build_executor_interface import BuildExecutorInterface
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from resolver.interface.args_resolver_interface import ArgsResolverInterface


class BuildModuleInterface(ModuleInterface):

    def __init__(self,
                 args_dict: dict,
                 args_resolver: ArgsResolverInterface,
                 preloader: PreloadInterface,
                 loader: LoadInterface,
                 target_generator: BuildFileGeneratorInterface,
                 target_compiler: BuildExecutorInterface):
        
        super().__init__(args_dict, args_resolver)
        self._loader = loader
        self._preloader = preloader
        self._target_generator = target_generator
        self._target_compiler = target_compiler

    @property
    def preloader(self):
        return self._preloader

    @property
    def loader(self):
        return self._loader

    @property
    def target_generator(self):
        return self._target_generator

    @property
    def target_compiler(self):
        return self._target_compiler

    def run(self):
        try:
            self._prebuild()
            self._preload()
            self._load()
            self._pre_target_generate()
            self._target_generate()
            self._post_target_generate()
            self._pre_target_compilation()
            self._target_compilation()
        except OHOSException as exception:
            raise exception
        else:
            self._post_target_compilation()
        finally:
            self._post_build()

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
    def _pre_target_generate(self):
        pass

    @abstractmethod
    def _target_generate(self):
        pass

    @abstractmethod
    def _post_target_generate(self):
        pass

    @abstractmethod
    def _pre_target_compilation(self):
        pass

    @abstractmethod
    def _target_compilation(self):
        pass

    @abstractmethod
    def _post_target_compilation(self):
        pass

    @abstractmethod
    def _post_build(self):
        pass
