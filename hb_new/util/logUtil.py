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

import sys

from containers.colors import Colors
from helper.noInstance import NoInstance

class LogUtil(metaclass=NoInstance):
    
    @staticmethod            
    def hb_info(msg):
        level = 'info'
        for line in str(msg).splitlines():
            sys.stdout.write(LogUtil.message(level, line))
            sys.stdout.flush()

    @staticmethod
    def hb_warning(msg):
        level = 'warning'
        for line in str(msg).splitlines():
            sys.stderr.write(LogUtil.message(level, line))
            sys.stderr.flush()
    
    @staticmethod
    def hb_error(msg):
        level = 'error'
        for line in str(msg).splitlines():
            sys.stderr.write(LogUtil.message(level, line))
            sys.stderr.flush()
    
    @staticmethod        
    def message(level, msg):
        if isinstance(msg, str) and not msg.endswith('\n'):
            msg += '\n'
        if level == 'error':
            msg = msg.replace('error:', f'{Colors.ERROR}error{Colors.END}:')
            return f'{Colors.ERROR}[OHOS {level.upper()}]{Colors.END} {msg}'
        elif level == 'info':
            return f'[OHOS {level.upper()}] {msg}'
        else:
            return f'{Colors.WARNING}[OHOS {level.upper()}]{Colors.END} {msg}'

    @staticmethod
    def write_log(log_path, msg, level):
        with open(log_path, 'at', encoding='utf-8') as log_file:
            for line in str(msg).splitlines():
                sys.stderr.write(LogUtil.message(level, line))
                sys.stderr.flush()
                log_file.write(LogUtil.message(level, line))
