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
#

from abc import ABCMeta, abstractmethod
from resolver.interface.args_resolver_interface import ArgsResolverInterface


class ModuleInterface(metaclass=ABCMeta):

    def __init__(self, args_dict: dict, args_resolver: ArgsResolverInterface):
        self._args_dict = args_dict
        self._args_resolver = args_resolver

    @property
    def args_resolver(self):
        return self._args_resolver

    @property
    def args_dict(self) -> dict:
        return self._args_dict

    @abstractmethod
    def run(self):
        pass
