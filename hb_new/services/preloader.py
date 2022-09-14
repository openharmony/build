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

import sys 
from containers.statusCode import StatusCode
from services.interface.preloadInterface import PreloadInterface
from resources.config import Config

from lite.hb_internal.preloader.preloader import Preloader
from hb_internal.common.config import Config as _Config


class PreloaderAdapt(PreloadInterface):
    
    def __init__(self, config) -> None:
        super().__init__(config)
        self.preloader = Preloader(_Config())
        
    def _internel_run(self) -> StatusCode:
        return self.preloader.run()

class OHOSPreloader(PreloadInterface):

    def __init__(self, config: Config):
        super().__init__(config)

    def _internel_run(self) -> StatusCode:
        self._generate_build_prop()
        self._generate_build_config_json()
        self._generate_parts_json()
        self._generate_parts_config_json()
        self._generate_build_gnargs_prop()
        self._generate_features_json()
        self._generate_syscap_json()
        self._generate_exclusion_modules_json()
        self._generate_platforms_build()
        self._generate_systemcapability_json()

    def _generate_build_prop(self) -> StatusCode: 
        pass

    def _generate_build_config_json(self) -> StatusCode:
        pass

    def _generate_parts_json(self) -> StatusCode:
        pass

    def _generate_parts_config_json(self) -> StatusCode:
        pass

    def _generate_build_gnargs_prop(self) -> StatusCode:
        pass

    def _generate_features_json(self) -> StatusCode:
        pass

    def _generate_syscap_json(self) -> StatusCode:
        pass

    def _generate_exclusion_modules_json(self) -> StatusCode:
        pass

    def _generate_subsystem_config_json(self) -> StatusCode:
        pass

    def _generate_platforms_build(self) -> StatusCode:
        pass

    def _generate_systemcapability_json(self) -> StatusCode:
        pass
