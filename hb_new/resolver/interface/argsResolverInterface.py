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

from abc import ABCMeta

from containers.arg import Arg
from exceptions.ohosException import OHOSException
from containers.status import throw_exception


class ArgsResolverInterface(metaclass=ABCMeta):

    def __init__(self, args_dict: dict):
        self._argsToFunction = dict()
        self._mapArgsToFunction(args_dict)

    @throw_exception
    def resolveArg(self, targetArg: Arg, module):
        if targetArg.argName not in self._argsToFunction.keys():
            raise OHOSException('You are tring to call {} resolve function, but it has not been defined yet', '0000')
        if not hasattr(self._argsToFunction[targetArg.argName], '__call__'):
            raise OHOSException()

        resolveFunction = self._argsToFunction[targetArg.argName]
        return resolveFunction(targetArg, module)

    @throw_exception
    def _mapArgsToFunction(self, args_dict: dict):
        for entity in args_dict.values():
            if isinstance(entity, Arg):
                argsName = entity.argName
                functionName = entity.resolveFuntion
                if not hasattr(self, functionName) or \
                        not hasattr(self.__getattribute__(functionName), '__call__'):
                    raise OHOSException(
                        'There is no resolution function for arg: {}'.format(
                            argsName),
                        "0004")
                entity.resolveFuntion = self.__getattribute__(functionName)
                self._argsToFunction[argsName] = self.__getattribute__(
                    functionName)
