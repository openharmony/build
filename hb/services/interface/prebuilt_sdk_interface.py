#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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

import os
from abc import abstractmethod
from services.interface.service_interface import ServiceInterface
from resources.config import Config


class PrebuiltSdkInterface(ServiceInterface):

    def __init__(self):
        super().__init__()
        self._config = Config()

    @property
    def config(self):
        return self._config

    def run(self):
        pass

    @abstractmethod
    def should_build_sdk(self, args_dict) -> bool:
        pass

    @abstractmethod
    def build_prebuilt_sdk(self, args_dict) -> bool:
        pass

    @abstractmethod
    def _execute_sdk_build(self, build_args: dict) -> bool:
        pass

    @abstractmethod
    def _post_process_sdk(self, api_version: str) -> bool:
        pass

    @abstractmethod
    def _migrate_legacy_sdk(self) -> None:
        pass