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

import re
import os
import subprocess
from datetime import datetime

from helper.noInstance import NoInstance

from util.logUtil import LogUtil
from exceptions.ohosException import OHOSException

class SystemUtil(metaclass=NoInstance):
    
    @staticmethod
    def exec_command(cmd, log_path='out/build.log', **kwargs):
        useful_info_pattern = re.compile(r'\[\d+/\d+\].+')
        is_log_filter = kwargs.pop('log_filter', False)

        with open(log_path, 'at', encoding='utf-8') as log_file:
            process = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    encoding='utf-8',
                                    **kwargs)
            for line in iter(process.stdout.readline, ''):
                if is_log_filter:
                    info = re.findall(useful_info_pattern, line)
                    if len(info):
                        LogUtil.hb_info(info[0])
                else:
                    LogUtil.hb_info(line)
                log_file.write(line)

        process.wait()
        ret_code = process.returncode

        if ret_code != 0:
            if is_log_filter:
                SystemUtil.get_failed_log(log_path)
            raise OHOSException('Please check build log in {}'.format(log_path))
        
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
    def get_current_time(type='default'):
        if type == 'timestamp':
            return int(datetime.utcnow().timestamp() * 1000)
        if type == 'datetime':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return datetime.now().replace(microsecond=0)
