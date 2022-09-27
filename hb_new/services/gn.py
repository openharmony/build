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
import os
import platform
from argparse import Namespace
from enum import Enum

from lite.hb_internal.common.config import Config as _Config
from lite.hb_internal.common.device import Device
from lite.hb_internal.common.product import Product

from containers.statusCode import StatusCode
from exceptions.ohosException import OHOSException
from services.interface.buildFileGeneratorInterface import BuildFileGeneratorInterface
from resources.config import Config
from util.systemUtil import SystemUtil
from util.ioUtil import IoUtil
from util.productUtil import ProductUtil
from util.logUtil import LogUtil


class GnAdapter(BuildFileGeneratorInterface):

    def __init__(self, config: Config, args: Namespace):
        super().__init__(config)
        self._args = args
        self._args_list = []
        self.config = _Config()

    def _internel_run(self) -> StatusCode:
        self._regist_all_args()
        self.gn_build(vars(self._args))

    def gn_build(self, cmd_args):
        # Gn cmd init and execute
        if self.config.os_level == "standard":
            gn_path = 'gn'
        else:
            gn_path = self.config.gn_path
        gn_args = cmd_args.get('gn', [])
        if cmd_args.get('log_level') == 'debug':
            gn_args.append('-v')
            gn_args.append(
                '--tracelog={}/gn_trace.log'.format(self.config._out_path))
        os_level = self.config.os_level
        if cmd_args.get('build_variant'):
            self.register_args('build_variant', cmd_args.get('build_variant'))
        gn_cmd = [
            gn_path,
            'gen',
            '--args={}'.format(" ".join(self._args_list)),
            self.config.out_path,
        ] + gn_args
        if os_level == 'mini' or os_level == 'small':
            gn_cmd.append(f'--script-executable={sys.executable}')

        LogUtil.hb_info('Excuting gn command: {}'.format(' '.join(gn_cmd)))
        SystemUtil.exec_command(
            gn_cmd, log_path=self.config.log_path, env=self.env())

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

    def _regist_all_args(self):
        if Device.get_compiler(self.config.device_path) != '':
            self.register_args('ohos_build_compiler_specified',
                               Device.get_compiler(self.config.device_path))
        self.register_args('product_path', self.config.product_path)
        self.register_args('product_name', self.config.product)
        if self.config.board:
            self.register_args('device_name', self.config.board)
        if self.config.target_cpu:
            self.register_args('target_cpu', self.config.target_cpu)
        if self.config.target_os:
            self.register_args('target_os', self.config.target_os)
        if self.config.os_level:
            self.register_args(f'is_{self.config.os_level}_system',
                               'true')
        if self.config.product == 'ohos-sdk':
            self.register_args('build_ohos_sdk', 'true')
            self.register_args('build_ohos_ndk', 'true')
        self.register_args('device_path', self.config.device_path)
        self.register_args('device_config_path',
                           self.config.device_config_path)
        self.register_args('product_config_path',
                           self.config.product_config_path)
        if self.config.os_level != "standard":
            self.register_args('device_company',
                               self.config.device_company)
        if self.config.kernel:
            self.register_args('ohos_kernel_type', self.config.kernel)

        self._args_list += Product.get_features(self.config.product_json)

    def register_args(self, args_name, args_value, quota=True):
        quota = False if args_value in ['true', 'false'] else quota
        if quota:
            if isinstance(args_value, list):
                self._args_list += [
                    '{}="{}"'.format(args_name, "&&".join(args_value))
                ]
            else:
                self._args_list += ['{}="{}"'.format(args_name, args_value)]
        else:
            self._args_list += ['{}={}'.format(args_name, args_value)]
        if args_name == 'ohos_build_target' and len(args_value):
            self.config.fs_attr = None


class CMDTYPE(Enum):
    GEN = 1
    PATH = 2
    DESC = 3
    LS = 4
    REFS = 5
    FORMAT = 6
    CLEAN = 7


class Gn(BuildFileGeneratorInterface):

    def __init__(self, config: Config):
        super().__init__(config)
        self._regist_gn_path()

    def _internel_run(self) -> StatusCode:
        self._regist_product_information()
        self._regist_product_features()
        self._regist_timestamp()
        self.execute_gn_cmd(CMDTYPE.GEN)

    def execute_gn_cmd(self, cmd_type: int, **kwargs) -> StatusCode:
        if cmd_type == CMDTYPE.GEN:
            return self._execute_gn_gen_cmd()
        elif cmd_type == CMDTYPE.PATH:
            return self._execute_gn_path_cmd(kwargs)
        elif cmd_type == CMDTYPE.DESC:
            return self._execute_gn_desc_cmd(kwargs)
        elif cmd_type == CMDTYPE.LS:
            return self._execute_gn_ls_cmd(kwargs)
        elif cmd_type == CMDTYPE.REFS:
            return self._execute_gn_refs_cmd(kwargs)
        elif cmd_type == CMDTYPE.FORMAT:
            return self._execute_gn_format_cmd(kwargs)
        elif cmd_type == CMDTYPE.CLEAN:
            return self._execute_gn_clean_cmd(kwargs)
        else:
            return StatusCode(False, 'Unsupported gn cmd type')

    '''Description: Get gn excutable path and regist it
    @parameter: none
    @return: StatusCode
    '''

    def _regist_gn_path(self) -> StatusCode:
        config_data = IoUtil.read_json_file(os.path.join(
            self.config.root_path, 'build/prebuilts_download_config.json'))
        copy_config_list = config_data[os.uname().sysname.lower(
        )][os.uname().machine.lower()]['copy_config']

        gn_path = ''
        for config in copy_config_list:
            if config['unzip_filename'] == 'gn':
                gn_path = os.path.join(
                    self.config.root_path, config['unzip_dir'], 'gn')
                break

        if os.path.exists(gn_path):
            self.exec = gn_path
            return StatusCode()
        return StatusCode(False, 'There is no gn executable file at {}, \
                          please execute build/prebuilts_download.sh'.format(gn_path))

    '''Description: Convert all registed args into a list
    @parameter: none
    @return: list of all registed args
    '''

    def _convert_args(self) -> list:
        args_list = []

        for key, value in self.args_dict.items():
            if isinstance(value, bool):
                args_list.append('{}={}'.format(key, str(value)).lower())

            elif isinstance(value, str):
                args_list.append('{}="{}"'.format(key, value))

            elif isinstance(value, int):
                args_list.append('{}={}'.format(key, value))

        return args_list

    '''Description: Regist compiling product features to gn command args, See features defination
    @parameter: none
    @return: none
    '''

    def _regist_product_features(self):
        features_dict = ProductUtil.get_features_dict(self.config.product_json)

        for key, value in features_dict.items():
            self.regist_arg(key, value)

    '''Description: Regist compiling product information to gn args
    @parameter: none
    @return: none
    '''

    def _regist_product_information(self):
        self.regist_arg('product_name', self.config.product)
        self.regist_arg('product_path', self.config.product_path)
        self.regist_arg('product_config_path', self.config.product_config_path)

        self.regist_arg('device_name', self.config.board)
        self.regist_arg('device_path', self.config.device_path)
        self.regist_arg('device_company', self.config.device_company)
        self.regist_arg('device_config_path', self.config.device_config_path)

        self.regist_arg('target_cpu', self.config.target_cpu)
        self.regist_arg('is_{}_system'.format(self.config.os_level), True)

        self.regist_arg('ohos_kernel_type', self.config.kernel)
        self.regist_arg('ohos_build_compiler_specified',
                        ProductUtil.get_compiler(self.config.device_path))

        if ProductUtil.get_compiler(self.config.device_path) == 'clang':
            self.regist_arg('ohos_build_compiler_dir', self.config.clang_path)

    def _regist_timestamp(self):
        self.regist_arg('ohos_build_time',
                        SystemUtil.get_current_time(type='timestamp'))
        self.regist_arg('ohos_build_datetime',
                        SystemUtil.get_current_time(type='datetime'))

    '''Description: Execute 'gn gen' command using registed args
    @parameter: kwargs TBD
    @return: StatusCode
    '''

    def _execute_gn_gen_cmd(self, **kwargs) -> StatusCode:
        gn_gen_cmd = [self.exec, 'gen',
                      '--args={}'.format(' '.join(self._convert_args())),
                      self.config.out_path]
        if self.config.os_level == 'mini' or self.config.os_level == 'small':
            gn_gen_cmd.append(f'--script-executable={sys.executable}')
        try:
            LogUtil.write_log(self.config.log_path, 'Excuting gn command: {} {} --args="{}" {}'.format(
                self.exec, 'gen', ' '.join(self._convert_args()).replace('"', "\\\""), ' '.join(gn_gen_cmd[3:])), 'info')
            SystemUtil.exec_command(gn_gen_cmd, self.config.log_path)
        except OHOSException:
            return StatusCode(False, '')

    def _execute_gn_path_cmd(self, **kwargs) -> StatusCode:
        pass

    def _execute_gn_desc_cmd(self, **kwargs) -> StatusCode:
        pass

    def _execute_gn_ls_cmd(self, **kwargs) -> StatusCode:
        pass

    def _execute_gn_refs_cmd(self, **kwargs) -> StatusCode:
        pass

    def _execute_gn_format_cmd(self, **kwargs) -> StatusCode:
        pass

    def _execute_gn_clean_cmd(self, **kwargs) -> StatusCode:
        pass
