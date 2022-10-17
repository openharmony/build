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

from containers.loader_outputs import LoaderOutputs
from services.interface.serviceInterface import ServiceInterface
from resources.config import Config


class LoadInterface(ServiceInterface):

    def __init__(self):
        super().__init__()
        self._config = Config()
        self._outputs = LoaderOutputs(self._config.root_path)

    @property
    def config(self):
        return self._config

    @property
    def outputs(self):
        return self._outputs

    def run(self):
        self.__post_init__()
        self._execute_loader_args_display()
        self._check_parts_config_info()
        self._generate_subsystem_configs()
        self._generate_target_platform_parts()
        self._generate_system_capabilities()
        self._generate_stub_targets()
        self._generate_platforms_part_by_src()
        self._generate_target_gn()
        self._generate_phony_targets_build_file()
        self._generate_required_parts_targets()
        self._generate_required_parts_targets_list()
        self._generate_src_flag()
        self._generate_auto_install_part()
        self._generate_platforms_list()
        self._generate_part_different_info()
        self._generate_infos_for_testfwk()
        self._check_product_part_feature()
        self._generate_syscap_files()

    @abstractmethod
    def __post_init__():
        pass

    @abstractmethod
    def _execute_loader_args_display():
        pass

    @abstractmethod
    def _check_parts_config_info():
        pass

    @abstractmethod
    def _generate_subsystem_configs():
        pass

    @abstractmethod
    def _generate_target_platform_parts():
        pass

    @abstractmethod
    def _generate_system_capabilities():
        pass

    @abstractmethod
    def _generate_stub_targets():
        pass

    @abstractmethod
    def _generate_platforms_part_by_src():
        pass

    @abstractmethod
    def _generate_target_gn():
        pass

    @abstractmethod
    def _generate_phony_targets_build_file():
        pass

    @abstractmethod
    def _generate_required_parts_targets():
        pass

    @abstractmethod
    def _generate_required_parts_targets_list():
        pass

    @abstractmethod
    def _generate_src_flag():
        pass

    @abstractmethod
    def _generate_auto_install_part():
        pass

    @abstractmethod
    def _generate_platforms_list():
        pass

    @abstractmethod
    def _generate_part_different_info():
        pass

    @abstractmethod
    def _generate_infos_for_testfwk():
        pass

    @abstractmethod
    def _check_product_part_feature():
        pass

    @abstractmethod
    def _generate_syscap_files():
        pass
