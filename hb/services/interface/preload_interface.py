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

from abc import abstractmethod
from services.interface.service_interface import ServiceInterface
from resources.config import Config
from util.log_util import LogUtil


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

    def regist_arg(self, arg_name: str, arg_value: str):
        if arg_name in self._args_dict.keys() and self._args_dict[arg_name] != arg_value:
            LogUtil.hb_warning('duplicated regist arg {}, the original value "{}" will be replace to "{}"'.format(
                arg_name, self._args_dict[arg_name], arg_value))

        self._args_dict[arg_name] = arg_value

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
        self._generate_compile_standard_whitelist_json()

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
