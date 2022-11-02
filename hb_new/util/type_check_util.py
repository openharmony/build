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

from exceptions.ohos_exception import OHOSException
from helper.noInstance import NoInstance


class TypeCheckUtil(metaclass=NoInstance):

    @staticmethod
    def check_arg_type(arg_object, target_class):
        if not isinstance(arg_object, target_class):
            raise OHOSException(f'type error')

    @staticmethod
    def is_bool_type(value):
        if isinstance(value, bool):
            return True
        elif isinstance(value, str):
            return value in ['true', 'True', 'false', 'False']
        else:
            return False

    @staticmethod
    def is_int_type(value):
        if isinstance(value, int):
            return True
        elif isinstance(value, str):
            return value.isdigit()
        else:
            return False

    @staticmethod
    def tile_list(value: list) -> list:
        result = []
        for entity in value:
            if isinstance(entity, list):
                result += TypeCheckUtil.tile_list(entity)
            elif isinstance(entity, str):
                result.append(entity)
            else:
                pass
        return result
