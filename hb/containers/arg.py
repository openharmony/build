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

import os
import argparse
import sys

from enum import Enum
from resources.global_var import CURRENT_ARGS_DIR
from resources.global_var import CURRENT_BUILD_ARGS
from resources.global_var import DEFAULT_BUILD_ARGS
from resources.global_var import CURRENT_SET_ARGS
from resources.global_var import DEFAULT_SET_ARGS
from resources.global_var import CURRENT_CLEAN_ARGS
from resources.global_var import DEFAULT_CLEAN_ARGS
from resources.global_var import DEFAULT_ENV_ARGS
from resources.global_var import CURRENT_ENV_ARGS
from resources.global_var import DEFAULT_TOOL_ARGS
from resources.global_var import CURRENT_TOOL_ARGS
from resources.global_var import ARGS_DIR
from exceptions.ohos_exception import OHOSException
from util.log_util import LogUtil
from util.io_util import IoUtil
from util.type_check_util import TypeCheckUtil
from resolver.args_factory import ArgsFactory
from containers.status import throw_exception


class ModuleType(Enum):

    BUILD = 0
    SET = 1
    ENV = 2
    CLEAN = 3
    TOOL = 4


class ArgType():

    NONE = 0
    BOOL = 1
    INT = 2
    STR = 3
    LIST = 4
    DICT = 5
    SUBPARSERS = 6

    @staticmethod
    def get_type(value: str):
        if value == 'bool':
            return ArgType.BOOL
        elif value == "int":
            return ArgType.INT
        elif value == 'str':
            return ArgType.STR
        elif value == "list":
            return ArgType.LIST
        elif value == 'dict':
            return ArgType.DICT
        elif value == 'subparsers':
            return ArgType.SUBPARSERS
        else:
            return ArgType.NONE


class BuildPhase():

    NONE = 0
    PRE_BUILD = 1
    PRE_LOAD = 2
    LOAD = 3
    PRE_TARGET_GENERATE = 4
    TARGET_GENERATE = 5
    POST_TARGET_GENERATE = 6
    PRE_TARGET_COMPILATION = 7
    TARGET_COMPILATION = 8
    POST_TARGET_COMPILATION = 9
    POST_BUILD = 10

    @staticmethod
    def get_type(value: str):
        if value == 'prebuild':
            return BuildPhase.PRE_BUILD
        elif value == "preload":
            return BuildPhase.PRE_LOAD
        elif value == 'load':
            return BuildPhase.LOAD
        elif value == "preTargetGenerate":
            return BuildPhase.PRE_TARGET_GENERATE
        elif value == 'targetGenerate':
            return BuildPhase.TARGET_GENERATE
        elif value == 'postTargetGenerate':
            return BuildPhase.POST_TARGET_GENERATE
        elif value == 'preTargetCompilation':
            return BuildPhase.PRE_TARGET_COMPILATION
        elif value == 'targetCompilation':
            return BuildPhase.TARGET_COMPILATION
        elif value == 'postTargetCompilation':
            return BuildPhase.POST_TARGET_COMPILATION
        elif value == 'postbuild':
            return BuildPhase.POST_BUILD
        else:
            return BuildPhase.NONE


class CleanPhase():

    REGULAR = 0
    DEEP = 1
    NONE = 2

    @staticmethod
    def get_type(value: str):
        if value == 'regular':
            return CleanPhase.REGULAR
        elif value == 'deep':
            return CleanPhase.DEEP
        else:
            return CleanPhase.NONE


class Arg():

    def __init__(self, name: str, helps: str, phase: str,
                 attribute: dict, argtype: ArgType, value,
                 resolve_function: str):
        self._arg_name = name
        self._arg_help = helps
        self._arg_phase = phase
        self._arg_attribute = attribute
        self._arg_type = argtype
        self._arg_value = value
        self._resolve_function = resolve_function

    @property
    def arg_name(self):
        return self._arg_name

    @property
    def arg_value(self):
        return self._arg_value

    @arg_value.setter
    def arg_value(self, value):
        self._arg_value = value

    @property
    def arg_help(self):
        return self._arg_help

    @property
    def arg_attribute(self):
        return self._arg_attribute

    @property
    def arg_phase(self):
        return self._arg_phase

    @property
    def arg_type(self):
        return self._arg_type

    @property
    def resolve_function(self):
        return self._resolve_function

    @resolve_function.setter
    def resolve_function(self, value):
        self._resolve_function = value

    @staticmethod
    @throw_exception
    def create_instance_by_dict(data: dict):
        arg_name = str(data['arg_name']).replace("-", "_")[2:]
        arg_help = str(data['arg_help'])
        arg_phase = BuildPhase.get_type(str(data['arg_phase']))
        arg_attibute = dict(data['arg_attribute'])
        arg_type = ArgType.get_type(data['arg_type'])
        arg_value = ''
        if arg_type == ArgType.BOOL:
            arg_value = data['argDefault']
        elif arg_type == ArgType.INT:
            arg_value = int(data['argDefault'])
        elif arg_type == ArgType.STR:
            arg_value = data['argDefault']
        elif arg_type == ArgType.LIST:
            arg_value = list(data['argDefault'])
        elif arg_type == ArgType.DICT:
            arg_value = dict(data['argDefault'])
        elif arg_type == ArgType.SUBPARSERS:
            arg_value = list(data['argDefault'])
        else:
            raise OHOSException('Unknown arg type "{}" for arg "{}"'.format(
                arg_type, arg_name), "0003")
        resolve_function = data['resolve_function']
        return Arg(arg_name, arg_help, arg_phase, arg_attibute, arg_type, arg_value, resolve_function)

    @staticmethod
    def get_help(module_type: ModuleType) -> str:
        parser = argparse.ArgumentParser()
        all_args = Arg.read_args_file(module_type)

        for arg in all_args.values():
            arg = dict(arg)
            ArgsFactory.genetic_add_option(parser, arg)

        parser.usage = 'hb {} [option]'.format(module_type.name.lower())
        parser.parse_known_args(sys.argv[2:])

        return parser.format_help()

    @staticmethod
    def parse_all_args(module_type: ModuleType) -> dict:
        args_dict = {}
        parser = argparse.ArgumentParser()
        all_args = Arg.read_args_file(module_type)

        for arg in all_args.values():
            arg = dict(arg)
            ArgsFactory.genetic_add_option(parser, arg)
            oh_arg = Arg.create_instance_by_dict(arg)
            args_dict[oh_arg.arg_name] = oh_arg

        parser.usage = 'hb {} [option]'.format(module_type.name.lower())
        parser_args = parser.parse_known_args(sys.argv[2:])

        for oh_arg in args_dict.values():
            if isinstance(oh_arg, Arg):
                assigned_value = parser_args[0].__dict__[oh_arg.arg_name]
                if oh_arg.arg_type == ArgType.LIST:
                    convert_assigned_value = TypeCheckUtil.tile_list(assigned_value)
                    convert_assigned_value = list(set(convert_assigned_value))
                elif oh_arg.arg_type == ArgType.SUBPARSERS:
                    convert_assigned_value = TypeCheckUtil.tile_list(assigned_value)
                    if len(convert_assigned_value):
                        convert_assigned_value = list(set(convert_assigned_value))
                        convert_assigned_value.extend(parser_args[1])
                        convert_assigned_value.sort(key=sys.argv[2:].index)
                elif oh_arg.arg_type == ArgType.BOOL:
                    if str(assigned_value).lower() == 'false':
                        convert_assigned_value = False
                    elif str(assigned_value).lower() == 'true' or assigned_value is None:
                        convert_assigned_value = True
                else:
                    convert_assigned_value = assigned_value

                if oh_arg.arg_attribute.get('deprecated', None) and oh_arg.arg_value != convert_assigned_value:
                    LogUtil.hb_warning(
                        'compile option "{}" will be deprecated, \
                            please consider use other options'.format(oh_arg.arg_name))
                oh_arg.arg_value = convert_assigned_value
                Arg.write_args_file(
                    oh_arg.arg_name, oh_arg.arg_value, module_type)

        return args_dict

    @staticmethod
    @throw_exception
    def write_args_file(key: str, value, module_type: ModuleType):
        args_file_path = ''
        if module_type == ModuleType.BUILD:
            args_file_path = CURRENT_BUILD_ARGS
        elif module_type == ModuleType.SET:
            args_file_path = CURRENT_SET_ARGS
        elif module_type == ModuleType.CLEAN:
            args_file_path = CURRENT_CLEAN_ARGS
        elif module_type == ModuleType.ENV:
            args_file_path = CURRENT_ENV_ARGS
        elif module_type == ModuleType.TOOL:
            args_file_path = CURRENT_TOOL_ARGS
        else:
            raise OHOSException(
                'You are trying to write args file, but there is no corresponding module "{}" args file'
                .format(module_type), "0002")
        args_file = Arg.read_args_file(module_type)
        args_file[key]["argDefault"] = value
        IoUtil.dump_json_file(args_file_path, args_file)

    @staticmethod
    @throw_exception
    def read_args_file(module_type: ModuleType):
        args_file_path = ''
        default_file_path = ''
        if module_type == ModuleType.BUILD:
            args_file_path = CURRENT_BUILD_ARGS
            default_file_path = DEFAULT_BUILD_ARGS
        elif module_type == ModuleType.SET:
            args_file_path = CURRENT_SET_ARGS
            default_file_path = DEFAULT_SET_ARGS
        elif module_type == ModuleType.CLEAN:
            args_file_path = CURRENT_CLEAN_ARGS
            default_file_path = DEFAULT_CLEAN_ARGS
        elif module_type == ModuleType.ENV:
            args_file_path = CURRENT_ENV_ARGS
            default_file_path = DEFAULT_ENV_ARGS
        elif module_type == ModuleType.TOOL:
            args_file_path = CURRENT_TOOL_ARGS
            default_file_path = DEFAULT_TOOL_ARGS
        else:
            raise OHOSException(
                'You are trying to read args file, but there is no corresponding module "{}" args file'
                .format(module_type.name.lower()), "0018")
        if not os.path.exists(CURRENT_ARGS_DIR):
            os.makedirs(CURRENT_ARGS_DIR, exist_ok=True)
        if not os.path.exists(args_file_path):
            IoUtil.copy_file(src=default_file_path, dst=args_file_path)
        return IoUtil.read_json_file(args_file_path)

    @staticmethod
    def clean_args_file():
        if os.path.exists(CURRENT_ARGS_DIR):
            for file in os.listdir(CURRENT_ARGS_DIR):
                if file.endswith('.json') and os.path.exists(os.path.join(CURRENT_ARGS_DIR, file)):
                    os.remove(os.path.join(CURRENT_ARGS_DIR, file))
