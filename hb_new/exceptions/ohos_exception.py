#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
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

import json

from resources.global_var import STATUS_FILE


class OHOSException(Exception):

    def __init__(self, message, code=0):
        super().__init__(message)
        self._code = code

    def get_solution(self) -> str:
        with open(STATUS_FILE, "r") as data:
            status_file = json.load(data)
            if not self._code in status_file.keys():
                return 'UNKNOWN REASON'
            return status_file[str(self._code)]['solution']
