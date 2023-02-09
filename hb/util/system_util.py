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
import re
import subprocess

from datetime import datetime

from util.log_util import LogUtil
from helper.noInstance import NoInstance
from exceptions.ohos_exception import OHOSException
from containers.status import throw_exception


class SystemUtil(metaclass=NoInstance):

    @staticmethod
    def exec_command(cmd: list, log_path='out/build.log', **kwargs):
        useful_info_pattern = re.compile(r'\[\d+/\d+\].+')
        is_log_filter = kwargs.pop('log_filter', False)
        if '' in cmd:
            cmd.remove('')
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
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
                LogUtil.get_failed_log(log_path)
            raise OHOSException(
                'Please check build log in {}'.format(log_path))

    @staticmethod
    def get_current_time(time_type='default'):
        if time_type == 'timestamp':
            return int(datetime.utcnow().timestamp() * 1000)
        if time_type == 'datetime':
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return datetime.now().replace(microsecond=0)
