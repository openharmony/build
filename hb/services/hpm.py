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

import shutil
import sys
import os
import time
import threading
from enum import Enum

from containers.status import throw_exception
from exceptions.ohos_exception import OHOSException
from services.interface.build_file_generator_interface import BuildFileGeneratorInterface
from containers.arg import Arg, ModuleType
from util.system_util import SystemUtil
from util.io_util import IoUtil
from util.log_util import LogUtil
from util.component_util import ComponentUtil
from resources.global_var import CURRENT_OHOS_ROOT


class CMDTYPE(Enum):
    BUILD = 1
    INSTALL = 2
    PACKAGE = 3
    PUBLISH = 4
    UPDATE = 5


class Hpm(BuildFileGeneratorInterface):

    def __init__(self):
        super().__init__()
        self._regist_hpm_path()

    def run(self):
        self.execute_hpm_cmd(CMDTYPE.BUILD)

    @throw_exception
    def execute_hpm_cmd(self, cmd_type: int, **kwargs):
        if cmd_type == CMDTYPE.BUILD:
            return self._execute_hpm_build_cmd()
        elif cmd_type == CMDTYPE.INSTALL:
            return self._execute_hpm_install_cmd()
        elif cmd_type == CMDTYPE.PACKAGE:
            return self._execute_hpm_pack_cmd()
        elif cmd_type == CMDTYPE.PUBLISH:
            return self._execute_hpm_publish_cmd()
        elif cmd_type == CMDTYPE.UPDATE:
            return self._execute_hpm_update_cmd()
        else:
            raise OHOSException(
                'You are tring to use an unsupported hpm cmd type "{}"'.format(cmd_type), '3001')

    '''Description: Get hpm excutable path and regist it
    @parameter: none
    @return: Status
    '''

    @throw_exception
    def _regist_hpm_path(self):
        hpm_path = shutil.which("hpm")
        if os.path.exists(hpm_path):
            self.exec = hpm_path
        elif os.path.exists(os.path.join(os.path.expanduser("~"), ".prebuilts_cache/hpm/node_modules/.bin/hpm")):
            self.exec = os.path.join(os.path.expanduser("~"), ".prebuilts_cache/hpm/node_modules/.bin/hpm")
        elif os.path.exists(os.path.join(CURRENT_OHOS_ROOT, ".prebuilts_cache/hpm/node_modules/.bin/hpm")):
            self.exec = os.path.join(CURRENT_OHOS_ROOT, ".prebuilts_cache/hpm/node_modules/.bin/hpm")
        else:
            raise OHOSException(
                'There is no hpm executable file at {}'.format(hpm_path), '0001')

    @throw_exception
    def _execute_hpm_build_cmd(self, **kwargs):
        if "-v" not in sys.argv:
            variant = 'default'
        else:
            variant = sys.argv[sys.argv.index("-v") + 1]
        logpath = os.path.join('out', variant, 'build.log')
        hpm_build_cmd = [self.exec, "build"] + self._convert_flags()
        SystemUtil.exec_command(hpm_build_cmd, log_path=logpath)

    @throw_exception
    def _execute_hpm_install_cmd(self, **kwargs):
        hpm_install_cmd = [self.exec, "install"] + self._convert_flags()
        SystemUtil.exec_command(hpm_install_cmd)

    @throw_exception
    def _execute_hpm_pack_cmd(self, **kwargs):
        hpm_pack_cmd = [self.exec, "pack", "-t"] + self._convert_flags()
        SystemUtil.exec_command(hpm_pack_cmd)

    @throw_exception
    def _execute_hpm_publish_cmd(self, **kwargs):
        hpm_publish_cmd = [self.exec, "publish", "-t"] + self._convert_flags()
        SystemUtil.exec_command(hpm_publish_cmd)

    @throw_exception
    def _execute_hpm_update_cmd(self, **kwargs):
        hpm_update_cmd = [self.exec, "update"] + self._convert_flags()
        SystemUtil.exec_command(hpm_update_cmd)

    '''Description: Convert all registed args into a list
    @parameter: none
    @return: list of all registed args
    '''

    def _convert_args(self) -> list:
        args_list = []

        for key, value in self.args_dict.items():
            if isinstance(value, bool):
                args_list.append('{}={}'.format(key, str(value).lower()))

            elif isinstance(value, str):
                args_list.append('{}="{}"'.format(key, value))

            elif isinstance(value, int):
                args_list.append('{}={}'.format(key, value))

            elif isinstance(value, list):
                args_list.append('{}="{}"'.format(key, "&&".join(value)))

        return args_list

    '''Description: Convert all registed flags into a list
    @parameter: none
    @return: list of all registed flags
    '''

    def _convert_flags(self) -> list:
        flags_list = []

        for key, value in self.flags_dict.items():
            # 部件参数无需参数名
            if key == "part_name":
                flags_list.append(str(value))
            else:
                if value == '':
                    flags_list.append('--{}'.format(key))
                elif key == 'path':
                    flags_list.extend(['--{}'.format(key), '{}'.format(str(value))])
                else:
                    flags_list.extend(['--{}'.format(key).lower(), '{}'.format(str(value)).lower()])

        return flags_list

    def _check_parts_validity(self, components: list):
        illegal_components = []
        for component in components:
            if not ComponentUtil.search_bundle_file(component):
                illegal_components.append(component)
        if illegal_components:
            raise OHOSException('ERROR argument "--parts": Invalid parts "{}". '.format(illegal_components))