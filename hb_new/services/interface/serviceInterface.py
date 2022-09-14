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

from abc import ABCMeta, abstractmethod
from containers.statusCode import StatusCode
from exceptions.ohosException import OHOSException


class ServiceInterface(metaclass=ABCMeta):

    def __init__(self):
        self._args_dict = {}
        self._exec = ''

    @property
    def args_dict(self):
        return self._args_dict

    @property
    def exec(self):
        return self._exec

    @exec.setter
    def exec(self, value):
        self._exec = value

    def regist_arg(self, argName: str, argValue: str) -> None:
        if argName in self._args_dict:
            raise OHOSException("duplicated regist arg {}".format(argName))

        self.args_dict[argName] = argValue

    @abstractmethod
    def run(self) -> StatusCode:
        pass
