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

from containers.statusCode import StatusCode
from services.interface.preloadInterface import PreloadInterface


class Preload():

    def __init__(self, preloader: PreloadInterface):
        self._preloader = preloader
    
    @property
    def unwrapped_preloader(self):
        return self._preloader
        
    def run(self) -> StatusCode:
        return self._preloader.run()
