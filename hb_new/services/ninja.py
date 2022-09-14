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
import platform

from lite.hb_internal.common.config import Config as _Config

from containers.statusCode import StatusCode
from services.interface.buildExecutorInterface import BuildExecutorInterface
from resources.config import Config
from util.systemUtil import SystemUtil

class NinjaAdapter(BuildExecutorInterface):

    def __init__(self, config: Config):
        super().__init__(config)
        self.config = _Config()

    def _internel_run(self) -> StatusCode:
        cmd_dict = dict()
        cmd_dict['ninja'] = {'default_target':'packages'}
        self.ninja_build(cmd_dict)
        
    def env(self):
        system = platform.system().lower()
        if self.config.os_level == 'standard':
            path = os.environ.get('PATH')
            my_python = os.path.join(
                self.config.root_path,
                f'prebuilts/python/{system}-x86/3.8.5/bin')
            os.environ['PATH'] = f'{my_python}:{path}'
        path = os.environ.get('PATH')
        my_build_tools = os.path.join(
            self.config.root_path, f'prebuilts/build-tools/{system}-x86/bin')
        os.environ['PATH'] = f'{my_build_tools}:{path}'
        return os.environ

    def ninja_build(self, cmd_args):
        if self.config.os_level == "standard":
            ninja_path = 'ninja'
        else:
            ninja_path = self.config.ninja_path

        ninja_args = cmd_args.get('ninja', {})
        my_ninja_args = []
        if ninja_args.get('verbose') == True or cmd_args.get('log_level') == 'debug':
            my_ninja_args.append('-v')
        if ninja_args.get('keep_ninja_going') == True:
            my_ninja_args.append('-k1000000')

        # Keep targets to the last
        if ninja_args.get('default_target') is not None:
            if self.config.os_level == "standard":
                if self.config.product == 'ohos-sdk':
                    my_ninja_args.append('build_ohos_sdk')
                else:
                    my_ninja_args.append('images')
            else:
                my_ninja_args.append('packages')
        if ninja_args.get('targets'):
            my_ninja_args.extend(ninja_args.get('targets'))
        ninja_cmd = [
            ninja_path, '-w', 'dupbuild=warn', '-C', self.config.out_path
        ] + my_ninja_args

        SystemUtil.exec_command(ninja_cmd,
                                log_path=self.config.log_path,
                                log_filter=True,
                                env=self.env())


class Ninja(BuildExecutorInterface):

    def __init__(self, config: Config):
        super().__init__(config)

    def _internel_run(self) -> StatusCode:
        pass
