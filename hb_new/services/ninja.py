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

from exceptions.ohosException import OHOSException
from services.interface.buildExecutorInterface import BuildExecutorInterface
from resources.config import Config
from util.systemUtil import SystemUtil
from util.ioUtil import IoUtil
from util.logUtil import LogUtil


class Ninja(BuildExecutorInterface):

    def __init__(self, config: Config):
        super().__init__(config)

    def _internel_run(self):
        self._regist_ninja_path()
        self._execute_ninja_cmd()

    def _execute_ninja_cmd(self):
        ninja_cmd = [self.exec, '-w', 'dupbuild=warn',
                     '-C', self.config.out_path] + self._convert_args()
        LogUtil.write_log(self.config.log_path,
                            'Excuting ninja command: {}'.format(' '.join(ninja_cmd)), 'info')
        try:
            SystemUtil.exec_command(ninja_cmd, self.config.log_path)
        except OHOSException:
            raise OHOSException('ninja error', '4000')

    def _convert_args(self) -> list:
        args_list = []
        for key, value in self._args_dict.items():
            if key == 'build_target' and isinstance(value, list):
                args_list += value
            else:
                if value == '':
                    args_list.insert(0, key)
                else:
                    args_list.insert(0, ' {}{} '.format(key, value))
        return args_list

    def _regist_ninja_path(self):
        config_data = IoUtil.read_json_file(os.path.join(
            self.config.root_path, 'build/prebuilts_download_config.json'))
        copy_config_list = config_data[os.uname().sysname.lower(
        )][os.uname().machine.lower()]['copy_config']

        gn_path = ''
        for config in copy_config_list:
            if config['unzip_filename'] == 'ninja':
                gn_path = os.path.join(
                    self.config.root_path, config['unzip_dir'], 'ninja')
                break

        if os.path.exists(gn_path):
            self.exec = gn_path
        else:
            raise OHOSException('There is no gn executable file at {}, \
                            please execute build/prebuilts_download.sh'.format(gn_path), '4000')
