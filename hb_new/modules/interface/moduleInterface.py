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
#

from abc import ABCMeta, abstractmethod

from util.typeCheckUtil import TypeCheckUtil
from resolver.interface.argsResolver import ArgsResolver
from containers.arg import Arg
from containers.statusCode import StatusCode


class ModuleInterface(metaclass=ABCMeta):

    def __init__(self, args: list, argsResolver: ArgsResolver):
        TypeCheckUtil.checkArgType(args[0], Arg)
        self._args = args
        self._argsResolver = argsResolver

    @property
    def argsResolver(self):
        return self._argsResolver

    @property
    def args(self):
        return self._args

    @abstractmethod
    def run(args) -> StatusCode:
        pass
