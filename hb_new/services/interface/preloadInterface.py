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

import os

from abc import abstractmethod

from containers.preloader_outputs import PrealoaderOutputs
from services.interface.serviceInterface import ServiceInterface
from resources.config import Config


class PreloadInterface(ServiceInterface):

    def __init__(self, config: Config):
        super().__init__()
        self._config = config    
        # TODO: We should provide ability to overide output to adapt each system  
        self._preloader_outputs = PrealoaderOutputs(os.path.join(config.root_path,'out/preloader', config.product))
        
    @property    
    def outputs(self):
        return self._preloader_outputs
    
    def run(self):
        self._internel_run()

    @abstractmethod
    def _internel_run(self):
        pass
