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

import os
import json
import importlib
import re
import shutil

from helper.noInstance import NoInstance
from exceptions.ohos_exception import OHOSException


class IoUtil(metaclass=NoInstance):

    @staticmethod
    def read_json_file(input_file) -> dict:
        if not os.path.isfile(input_file):
            raise OHOSException(f'{input_file} not found', '0008')

        with open(input_file, 'rb') as input_f:
            data = json.load(input_f)
            return data

    @staticmethod
    def dump_json_file(dump_file, json_data):
        with open(dump_file, 'wt', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=2)

    @staticmethod
    def read_file(file_path):
        if not os.path.exists(file_path):
            raise OHOSException(
                "file '{}' doesn't exist.".format(file_path), '0009')
        data = None
        with open(file_path, 'r') as input_f:
            data = input_f.read()
        return data

    @staticmethod
    def read_yaml_file(input_file):
        if not os.path.isfile(input_file):
            raise OHOSException(f'{input_file} not found', '0010')

        yaml = importlib.import_module('yaml')
        with open(input_file, 'rt', encoding='utf-8') as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    raise OHOSException(f'{input_file} load failed, error line:'
                                        f' {mark.line + 1}:{mark.column + 1}', '0011')
                else:
                    raise OHOSException(f'{input_file} load failed', '0011')

    @staticmethod
    def copy_file(src, dst):
        return shutil.copy(src, dst)
