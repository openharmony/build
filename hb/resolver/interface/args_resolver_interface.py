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

from abc import ABCMeta
from containers.arg import Arg
from exceptions.ohos_exception import OHOSException
from containers.status import throw_exception


class ArgsResolverInterface(metaclass=ABCMeta):

    def __init__(self, args_dict: dict):
        self._args_to_function = dict()
        self._map_args_to_function(args_dict)

    @throw_exception
    def resolve_arg(self, target_arg: Arg, module):
        if target_arg.arg_name not in self._args_to_function.keys():
            raise OHOSException(
                'You are tring to call {} resolve function, but it has not been defined yet', '0000')
        if not hasattr(self._args_to_function[target_arg.arg_name], '__call__'):
            raise OHOSException()

        resolve_function = self._args_to_function[target_arg.arg_name]
        return resolve_function(target_arg, module)

    @throw_exception
    def _map_args_to_function(self, args_dict: dict):
        for entity in args_dict.values():
            if isinstance(entity, Arg):
                args_name = entity.arg_name
                function_name = entity.resolve_function
                if not hasattr(self, function_name) or \
                        not hasattr(self.__getattribute__(function_name), '__call__'):
                    raise OHOSException(
                        'There is no resolution function for arg: {}'.format(
                            args_name),
                        "0004")
                entity.resolve_function = self.__getattribute__(function_name)
                self._args_to_function[args_name] = self.__getattribute__(
                    function_name)
