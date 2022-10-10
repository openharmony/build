#!/usr/bin/env python
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


class Output():

    def __init__(self, path: str, outcome: str, check_func=None):
        self._path = path
        self._outcome = outcome
        self._check_func = check_func
        self._is_produced = False

    def _check_output(self) -> bool:
        return os.path.exists(os.path.join(self._path, self._outcome))
    
    def check_output(self) -> bool:
        if self._check_func != None:
            self._is_produced = self._check_func(self)
        else:
            self._is_produced = self._check_output()
        return self._is_produced
            
