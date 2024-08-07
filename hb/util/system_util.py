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
import sys
import re
import subprocess

from datetime import datetime

from util.log_util import LogUtil
from hb.helper.no_instance import NoInstance
from exceptions.ohos_exception import OHOSException
from containers.status import throw_exception


class SystemUtil(metaclass=NoInstance):

    @staticmethod
    def exec_command(cmd: list, log_path='out/build.log', exec_env=None, log_mode='normal', **kwargs):
        useful_info_pattern = re.compile(r'\[\d+/\d+\].+')
        is_log_filter = kwargs.pop('log_filter', False)
        if log_mode == 'silent':
            is_log_filter = True
        if '' in cmd:
            cmd.remove('')
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if (sys.argv[1] == 'build' and 
            len(sys.argv) == 5 and 
            '-i' in sys.argv[3:] and 
            {'-t', '-test'} & set(sys.argv[3:])):
            cmd.extend(['-t', 'both'])
        if (sys.argv[1] == 'build' and 
            len(sys.argv) == 4 and 
            sys.argv[-1] == '-t'):
            cmd.extend(['-t', 'onlytest'])
        with open(log_path, 'at', encoding='utf-8') as log_file:
            LogUtil.hb_info("start run hpm command")
            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       encoding='utf-8',
                                       env=exec_env,
                                       **kwargs)
            for line in iter(process.stdout.readline, ''):
                log_file.write(line)
                if is_log_filter:
                    info = re.findall(useful_info_pattern, line)
                    if len(info):
                        LogUtil.hb_info(info[0], mode=log_mode)
                else:
                    LogUtil.hb_info(line)

        process.wait()
        LogUtil.hb_info("end hpm command")
        ret_code = process.returncode

        if ret_code != 0:
            LogUtil.get_failed_log(log_path)

    @staticmethod
    def get_current_time(time_type: str = 'default'):
        if time_type == 'timestamp':
            return int(datetime.utcnow().timestamp() * 1000)
        if time_type == 'datetime':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return datetime.now().replace(microsecond=0)


class ExecEnviron:
    def __init__(self):
        self._env = None

    @property
    def allenv(self):
        return self._env

    @property
    def allkeys(self):
        if self._env is None:
            return []
        return list(self._env.keys())

    def initenv(self):
        self._env = os.environ.copy()

    def allow(self, allowed_vars: list):
        if self._env is not None:
            allowed_env = {k: v for k, v in self._env.items() if k in allowed_vars}
            self._env = allowed_env
