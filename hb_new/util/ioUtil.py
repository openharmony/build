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

import os
import json
import importlib
import re
import sys
import shutil

from util.logUtil import LogUtil
from helper.noInstance import NoInstance
from exceptions.ohosException import OHOSException

class IoUtil(metaclass=NoInstance):
    
    @staticmethod
    def read_json_file(input_file):
        if not os.path.isfile(input_file):
            raise OHOSException(f'{input_file} not found')

        with open(input_file, 'rb') as input_f:
            data = json.load(input_f)
            return data
    
    @staticmethod    
    def dump_json_file(dump_file, json_data):
        with open(dump_file, 'wt', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=2)
        
    @staticmethod
    def read_yaml_file(input_file):
        if not os.path.isfile(input_file):
            raise OHOSException(f'{input_file} not found')

        yaml = importlib.import_module('yaml')
        with open(input_file, 'rt', encoding='utf-8') as yaml_file:
            try:
                return yaml.safe_load(yaml_file)
            except yaml.YAMLError as exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    raise OHOSException(f'{input_file} load failed, error line:'
                                        f' {mark.line + 1}:{mark.column + 1}')
                    
    @staticmethod
    def get_failed_log(log_path):
        with open(log_path, 'rt', encoding='utf-8') as log_file:
            data = log_file.read()
        failed_pattern = re.compile(
            r'(\[\d+/\d+\].*?)(?=\[\d+/\d+\]|'
            'ninja: build stopped)', re.DOTALL)
        failed_log = failed_pattern.findall(data)
        for log in failed_log:
            if 'FAILED:' in log:
                LogUtil.hb_error(log)

        failed_pattern = re.compile(r'(ninja: error:.*?)\n', re.DOTALL)
        failed_log = failed_pattern.findall(data)
        for log in failed_log:
            LogUtil.hb_error(log)

        error_log = os.path.join(os.path.dirname(log_path), 'error.log')
        if os.path.isfile(error_log):
            with open(error_log, 'rt', encoding='utf-8') as log_file:
                LogUtil.hb_error(log_file.read())
                
    @staticmethod
    def copy_file(src, dst):
        return shutil.copy(src, dst)
    

    