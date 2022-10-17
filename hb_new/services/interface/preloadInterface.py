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

from abc import abstractmethod

from services.interface.serviceInterface import ServiceInterface
from resources.config import Config


class PreloadInterface(ServiceInterface):

    def __init__(self):
        super().__init__()
        self._config = Config()

    @property
    def outputs(self):
        return self._preloader_outputs

    @property
    def config(self):
        return self._config

    def run(self):
        self.__post_init__()
        self._generate_build_prop()
        self._generate_build_config_json()
        self._generate_parts_json()
        self._generate_parts_config_json()
        self._generate_build_gnargs_prop()
        self._generate_features_json()
        self._generate_syscap_json()
        self._generate_exclusion_modules_json()
        self._generate_platforms_build()
        self._generate_subsystem_config_json()
        self._generate_systemcapability_json()

    @abstractmethod
    def __post_init__(self):
        pass

    @abstractmethod
    def _generate_build_prop(self):
        pass

    @abstractmethod
    def _generate_build_config_json(self):
        pass

    @abstractmethod
    def _generate_parts_json(self):
        pass

    @abstractmethod
    def _generate_parts_config_json(self):
        pass

    @abstractmethod
    def _generate_build_gnargs_prop(self):
        pass

    @abstractmethod
    def _generate_features_json(self):
        pass

    @abstractmethod
    def _generate_syscap_json(self):
        pass

    @abstractmethod
    def _generate_exclusion_modules_json(self):
        pass

    @abstractmethod
    def _generate_platforms_build(self):
        pass

    @abstractmethod
    def _generate_subsystem_config_json(self):
        pass

    @abstractmethod
    def _generate_systemcapability_json(self):
        pass
