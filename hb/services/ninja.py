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

from exceptions.ohos_exception import OHOSException
from services.interface.build_executor_interface import BuildExecutorInterface
from resources.config import Config
from util.system_util import SystemUtil, ExecEnviron
from util.io_util import IoUtil
from util.log_util import LogUtil

from util.kernel_permission import KernelPermission


class Ninja(BuildExecutorInterface):

    def __init__(self):
        super().__init__()
        self.config = Config()
        self._regist_ninja_path()

    def run(self):
        self._execute_ninja_cmd()

    def _execute_ninja_cmd(self):
        """execute ninja cmd using registed args
        :raise OHOSException: when ninja failed
        """
        ninja_cmd = [self.exec, '-w', 'dupbuild=warn',
                     '-C', self.config.out_path] + self._convert_args()
        LogUtil.write_log(self.config.log_path,
                          'Excuting ninja command: {}'.format(' '.join(ninja_cmd)), 'info')

        ninja_env = ExecEnviron()
        ninja_env_allowlist = IoUtil.read_json_file(
            os.path.join(
                self.config.root_path,
                "out/preloader",
                self.config.product,
                "compile_env_allowlist.json",
            )
        ).get("ninja")

        if ninja_env_allowlist:
            ninja_env.initenv()
            ninja_env.allow(ninja_env_allowlist)
            LogUtil.write_log(
                self.config.log_path,
                f"run ninja with environ {ninja_env.allkeys}",
                "info",
            )

        log_filter = os.getenv("LOG_FILTER", "True") == "True"
        SystemUtil.exec_command(
            ninja_cmd,
            self.config.log_path,
            exec_env=ninja_env.allenv,
            log_filter=log_filter,
            log_mode=self.config.log_mode
        )

        # run llvm-object --add-section .kernelpermission=json_file xx/xx.so
        KernelPermission.run(self.config.out_path, self.config.root_path)

    def _convert_args(self) -> list:
        """convert all registed args into a list
        """
        args_list = []
        for key, value in self._args_dict.items():
            if key == 'build_target' and isinstance(value, list):
                args_list += value
            elif key == 'ninja_args' and isinstance(value, list):
                args_list += value
            else:
                if value == '':
                    args_list.insert(0, key)
                else:
                    args_list.insert(0, ' {}{} '.format(key, value))
        return args_list

    def _regist_ninja_path(self):
        """find ninja executable
        :raise OHOSException: when can't find the ninja excutable
        """
        ninja_path = os.path.join(self.config.root_path, 'prebuilts/build-tools/{}-x86/bin/ninja'
                .format(sys.platform))
        if os.path.exists(ninja_path):
            self.exec = ninja_path
        else:
            raise OHOSException(
                'There is no gn executable file at {}'.format(ninja_path), '0001')
