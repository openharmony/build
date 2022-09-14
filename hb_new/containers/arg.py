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

from distutils.util import strtobool
from argparse import Namespace
class Arg():

    def __init__(self, name: str, help: str, phase: str, attribute: str, value: str, argtype: str):
        self._argName = name
        self._argHelp = help
        self._argPhase = phase
        self._argAttribute = attribute
        self._argValue = value
        self._argType = argtype

    @property
    def argName(self):
        return self._argName

    @property
    def argValue(self):
        return self._argValue
    
    @argValue.setter
    def argValue(self, value):
        self._argValue = value

    @property
    def argHelp(self):
        return self._argHelp

    @property
    def argAttribute(self):
        return self._argAttribute

    @property
    def argPhase(self):
        return self._argPhase
    
    @property
    def argType(self):
        return self._argType

    @staticmethod
    def createInstanceByDict(jsonDict):
        name = str(jsonDict['argName']).replace("-", "_")[2:]
        help = jsonDict['argHelp']
        phase = jsonDict['argPhase']
        attibute = jsonDict['argAttribute']
        arg_type = jsonDict['argType']
        default_value = strtobool(jsonDict['argDefault']) if jsonDict['argType'] == 'bool' else jsonDict['argDefault']
        return Arg(name, help, phase, attibute, default_value, arg_type)
    
    @staticmethod
    def createInstanceByArgparse(args_parser):
        pass
    
